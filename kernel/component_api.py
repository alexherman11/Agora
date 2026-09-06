"""Bind component commands to the one authenticated verb commit gateway.
Never: never appends events directly or accepts a commit function from generated code."""

from kernel import component_candidates, component_commands, component_data, component_testing
from kernel.facets import FacetError
from kernel.locking import synchronized
from kernel.store import Store


def bind(commit, refusal, authenticate):
    def _call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValueError, TypeError, KeyError, FacetError) as exc:
            raise refusal(str(exc)) from exc

    @synchronized
    def open_component_candidate(
        world: Store,
        actor: str,
        entity: str,
        revision: int | None = None,
        viewport: dict | None = None,
    ):
        authenticate(actor)
        return _call(component_candidates.open_candidate, world, actor, entity, revision, viewport)

    @synchronized
    def candidate_event(
        world: Store,
        actor: str,
        candidate: str,
        event: dict,
        fingerprint: str,
        local: dict | None = None,
        viewport: dict | None = None,
    ):
        authenticate(actor)
        return _call(
            component_candidates.interact,
            world,
            actor,
            candidate,
            event,
            fingerprint,
            local,
            viewport,
            commit,
        )

    @synchronized
    def close_component_candidate(world: Store, actor: str, candidate: str):
        authenticate(actor)
        return _call(component_candidates.close, world, actor, candidate)

    @synchronized
    def component_view(
        world: Store,
        actor: str,
        entity: str = "",
        revision: int | None = None,
        local: dict | None = None,
        viewport: dict | None = None,
    ):
        authenticate(actor)
        return _call(component_commands.frame, world, entity, revision, local, viewport)

    @synchronized
    def test_component(
        world: Store, actor: str, entity: str, cases: list, revision: int | None = None
    ):
        authenticate(actor)
        return _call(component_testing.test, world, actor, entity, revision, cases, commit)

    @synchronized
    def activate_component(
        world: Store, actor: str, entity: str, revision: int, expected_revision: int
    ):
        authenticate(actor)
        return _call(
            component_commands.activate, world, actor, entity, revision, expected_revision, commit
        )

    @synchronized
    def component_event(
        world: Store,
        actor: str,
        entity: str,
        revision: int,
        event: dict,
        fingerprint: str,
        local: dict | None = None,
        viewport: dict | None = None,
    ):
        authenticate(actor)
        return _call(
            component_commands.interact,
            world,
            actor,
            entity,
            revision,
            event,
            local,
            viewport,
            fingerprint,
            commit,
        )

    @synchronized
    def component_actions(world: Store, actor: str):
        authenticate(actor)
        return _call(component_data.actions, world)

    @synchronized
    def invoke_component(
        world: Store, actor: str, entity: str, revision: int, action: str, args: dict
    ):
        authenticate(actor)
        record = _call(component_data.admitted, world, entity, revision)
        return _call(
            component_commands.interact,
            world,
            actor,
            entity,
            revision,
            args,
            {},
            None,
            component_data.fingerprint(world, record),
            commit,
            action=action,
        )

    return {
        "open_component_candidate": open_component_candidate,
        "candidate_event": candidate_event,
        "close_component_candidate": close_component_candidate,
        "component_view": component_view,
        "test_component": test_component,
        "activate_component": activate_component,
        "component_event": component_event,
        "component_actions": component_actions,
        "invoke_component": invoke_component,
    }
