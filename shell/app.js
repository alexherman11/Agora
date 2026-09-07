"use strict";
const $ = (id) => document.getElementById(id);
let token,
  selection = null,
  current = null,
  preview = null,
  pageOffset = 0,
  generation = 0;
function notice(message = "") {
  $("notice").textContent = message;
}
async function api(path, body) {
  const response = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Agora-Session": token,
          },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
const command = (verb, args) => api("/verb", { verb, args });
async function refreshAgent() {
  const state = await api("/agent");
  const account = state.provider === "openai-account";
  $("agent-connection").textContent = account
    ? `${state.model === "gpt-6-astra" ? "Astra" : state.model} · ${state.signed_in ? "OpenAI account" : "Sign-in needed"}`
    : state.model;
  $("openai-login").hidden = !account || state.signed_in;
  return state.signed_in;
}
$("openai-login").onclick = async () => {
  // Open from the click gesture so browser popup protection does not lose the flow.
  const loginWindow = window.open("about:blank", "agora-openai-login");
  if (loginWindow) loginWindow.opener = null;
  try {
    const result = await api("/agent/login", {});
    if (result.signed_in) {
      loginWindow?.close();
      await refreshAgent();
      return;
    }
    if (loginWindow) loginWindow.location.href = result.url;
    else throw new Error("Allow popups for Agora, then try Sign in again.");
    const timer = setInterval(async () => {
      try { if (await refreshAgent()) clearInterval(timer); }
      catch { clearInterval(timer); }
    }, 3000);
    setTimeout(() => clearInterval(timer), 5 * 60 * 1000);
  } catch (error) {
    loginWindow?.close();
    notice(error.message);
  }
};
function say(text, cls) {
  const p = document.createElement("p");
  p.className = cls;
  p.textContent = text;
  $("log").append(p);
  $("log").scrollTop = $("log").scrollHeight;
}
function select(ref, label) {
  selection = ref;
  $("selection-status").textContent = ref
    ? `Selected: ${label || ref}`
    : "No object selected";
}
const components = window.AgoraComponents($("component-host"), command, notice, select,
  () => refresh().catch(e => notice(e.message)));
async function closePreview() {
  const candidate = preview?.candidate;
  preview = null;
  components.reset();
  if (candidate) await command("close_component_candidate", {candidate});
}
async function previewComponent(entity) {
  await closePreview();
  preview = {...(await command("open_component_candidate", {entity,viewport:components.viewport()})).result, kind:"component"};
  select(null);
}
async function refresh() {
  if (components.busy()) return;
  const serial = ++generation,
    tree = await api("/tree"),
    query = new URLSearchParams({ offset: pageOffset });
  if (preview && preview.kind !== "component") {
    query.set("entity", preview.entity);
    query.set("revision", preview.revision);
  }
  if (selection) query.set("selected", selection);
  let view;
  try {
    view = await api("/lens?" + query);
  } catch (error) {
    if (!selection) throw error;
    select(null);
    query.delete("selected");
    view = await api("/lens?" + query);
  }
  if (preview?.kind === "component" || (!preview && view.component)) {
    const result = preview?.kind === "component" ?
      (components.snapshot()?.candidate === preview.candidate ? {...preview,...components.snapshot()} : preview) :
      (await command("component_view", {local:components.local(),viewport:components.viewport()})).result;
    view = {...result, kind:"component", display_revision:view.display_revision};
  }
  if (serial !== generation) return;
  current = view;
  $("status").textContent = `Connected · world revision ${tree.revision}`;
  $("preview-bar").hidden = !preview;
  $("desk").hidden = view.active;
  $("lens").hidden = !view.active || view.kind === "component";
  $("component-host").hidden = !view.active || view.kind !== "component";
  $("inspector").hidden = !view.active;
  $("view-label").textContent = view.active
    ? `${preview ? "Preview" : view.kind === "component" ? "Authored component" : "Personal lens"} · r${view.revision}`
    : "Your desk";
  if (view.kind === "component" && view.active) {
    $("definition").textContent = JSON.stringify(view.definition, null, 2);
    components.show(view);
  } else {
    components.reset();
    if (view.active) renderLens(view);
    else renderDesk(tree);
  }
}
function renderLens(view) {
  const focusedEntity = document.activeElement?.dataset.entity;
  $("lens-title").textContent = view.definition.title;
  $("lens").className = view.definition.density || "comfortable";
  $("definition").textContent = JSON.stringify(view.definition, null, 2);
  $("rows").replaceChildren();
  for (const row of view.rows) {
    const button = document.createElement("button");
    button.className = "row";
    button.dataset.entity = row.entity;
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", row.entity === view.selected);
    const label = document.createElement("strong");
    label.textContent = row.label;
    button.append(label);
    if (row.secondary.length) {
      const small = document.createElement("small");
      small.textContent = row.secondary.join(" · ");
      button.append(small);
    }
    button.onclick = () => {
      select(row.entity, row.label);
      refresh().catch((e) => notice(e.message));
    };
    button.onkeydown = (event) => {
      if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
      event.preventDefault();
      const next =
        event.key === "ArrowDown"
          ? button.nextElementSibling
          : button.previousElementSibling;
      if (next) {
        next.focus();
        next.click();
      }
    };
    $("rows").append(button);
    if (row.entity === focusedEntity) button.focus();
  }
  const row = view.rows.find((r) => r.entity === view.selected);
  select(view.selected, row?.label);
  $("selected-label").textContent =
    row?.label ||
    (view.selected ? "Selected object" : "No objects in this view");
  $("detail").textContent = view.detail;
  $("page-status").textContent =
    `${view.total ? view.offset + 1 : 0}–${Math.min(view.offset + 100, view.total)} of ${view.total}`;
  $("previous-page").disabled = view.offset === 0;
  $("next-page").disabled = view.offset + 100 >= view.total;
}
function renderDesk(tree) {
  $("desk").replaceChildren();
  if (!tree.nodes.length) {
    const box = document.createElement("div");
    box.className = "empty";
    const title = document.createElement("h1");
    title.textContent = "Make yourself at home.";
    const text = document.createElement("p");
    text.textContent =
      "Add a note, bring your work here, or ask JEFF to help shape a view.";
    box.append(title, text);
    $("desk").append(box);
  }
  for (const node of tree.nodes) {
    const button = document.createElement("button");
    button.className = "item" + (node.entity === selection ? " selected" : "");
    button.style.left = node.transform.x + "px";
    button.style.top = node.transform.y + "px";
    const name = document.createElement("strong");
    name.textContent = node.label;
    const hint = document.createElement("small");
    hint.textContent = node.component ? "Executable component · Open isolated preview" : node.lens
      ? "Personal lens · Open preview"
      : "Select object";
    button.append(name, hint);
    button.onclick = async () => {
      try {
        select(node.entity, node.label);
        if (node.component) {
          await previewComponent(node.entity);
        } else if (node.lens) {
          preview = (await command("preview_lens", { entity: node.entity }))
            .result;
          select(null);
          pageOffset = 0;
        } else {
          say(
            JSON.stringify(
              (await command("read", { entity: node.entity })).result,
              null,
              2,
            ),
            "call",
          );
        }
        await refresh();
      } catch (e) {
        notice(e.message);
      }
    };
    $("desk").append(button);
  }
}
$("chat-form").onsubmit = async (event) => {
  event.preventDefault();
  const message = $("message").value.trim();
  if (!message) return;
  $("message").value = "";
  say(message, "user");
  $("send").disabled = true;
  notice();
  try {
    const result = await api("/chat", { message, selection });
    for (const call of result.calls)
      say(`${call.verb} ${call.error ? "· " + call.error : "✓"}`, "call");
    say(result.reply, "jeff");
    await refresh();
  } catch (e) {
    say(e.message, "error");
  } finally {
    $("send").disabled = false;
    refreshAgent().catch(() => {});
  }
};
$("suggest").onclick = () => {
  $("message").value =
    "Make my notes readable as a compact list, with a preview when I select one.";
  $("message").focus();
};
$("stop").onclick = () => {
  components.stop();
  api("/stop", {})
    .then(() => notice("Stopped JEFF and view input. Completed changes remain recorded. Use Default desk to recover."))
    .catch((e) => notice(e.message));
};
$("default").onclick = async () => {
  try {
    await command("activate_lens", { entity: "" });
    notice();
    await closePreview();
    select(null);
    pageOffset = 0;
    await refresh();
  } catch (e) {
    notice(e.message);
  }
};
$("restore").onclick = async () => {
  try {
    const record = (
      await command("read", { entity: "ent_desk", facet_type: "core.display" })
    ).result.facets["core.display"];
    const previous =
      record.revision > 1
        ? (
            await command("read", {
              entity: "ent_desk",
              facet_type: "core.display",
              revision: record.revision - 1,
            })
          ).result.facets["core.display"].body
        : { lens: "", revision: 0 };
    await command(previous.kind === "component" ? "activate_component" : "activate_lens", {
      entity: previous.lens,
      revision: previous.revision,
      expected_revision: record.revision,
    });
    notice();
    await closePreview();
    select(null);
    pageOffset = 0;
    await refresh();
  } catch (e) {
    notice(e.message);
  }
};
$("activate").onclick = async () => {
  try {
    await command(preview.kind === "component" ? "activate_component" : "activate_lens", {
      entity: preview.entity,
      revision: preview.revision,
      expected_revision: current.display_revision,
    });
    await closePreview();
    await refresh();
  } catch (e) {
    notice(e.message);
  }
};
$("close-preview").onclick = async () => {
  await closePreview();
  select(null);
  pageOffset = 0;
  refresh().catch((e) => notice(e.message));
};
$("draft").onclick = async () => {
  try {
    if (current.kind === "component") await previewComponent(current.entity);
    else preview = (await command("preview_lens", {entity:current.entity})).result;
    select(null);
    pageOffset = 0;
    await refresh();
  } catch (e) {
    notice(e.message);
  }
};
$("previous-page").onclick = () => {
  pageOffset = Math.max(0, pageOffset - 100);
  select(null);
  refresh().catch((e) => notice(e.message));
};
$("next-page").onclick = () => {
  pageOffset += 100;
  select(null);
  refresh().catch((e) => notice(e.message));
};
$("new-note").onclick = () => $("note-dialog").showModal();
$("cancel-note").onclick = () => $("note-dialog").close();
$("note-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    const note = await command("mint", {
      facets: {
        "core.name": { name: $("note-title").value },
        "core.text": { text: $("note-text").value },
      },
    });
    await command("place", { entity: note.result.entity });
    $("note-dialog").close();
    $("note-form").reset();
    await refresh();
  } catch (e) {
    notice(e.message);
  }
};
(async () => {
  try {
    token = (await api("/session")).token;
    await refresh();
    const stream = new EventSource("/events");
    refreshAgent().catch((e) => { $("agent-connection").textContent = e.message; });
    stream.addEventListener("changed", () =>
      refresh().catch((e) => notice(e.message)),
    );
    stream.onerror = () => {
      $("status").textContent = "Disconnected · reconnecting…";
    };
  } catch (e) {
    notice(e.message);
  }
})();
