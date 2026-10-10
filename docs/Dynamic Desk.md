> A system should be built with a minimum set of unchangeable parts; those parts should be as general as possible; and all parts of the system should be held in a uniform framework.
>
> If a system is to serve the creative spirit, it must be entirely comprehensible to a single individual.
>
> — Daniel H. H. Ingalls, *[Design Principles Behind Smalltalk](https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html)* (1981)

This document is the vision document for the first phase of development, a roughly coherent operating system that is designed for use on any device. This document holds the principles that are to be designed around, while Current Implementation holds our current technical composition, which is likely to change. This document changes slowly.

Modify this document only when:
- Something in this document is strained by the existing implementation, and we like the implementation.
- There is a good idea we don't have down that would improve the design overall
- We have good reason to change our stance on a principle due to new evidence.

Alex makes all final edits to this documents, agents may only propose.
## Overview

- **Strong**: we uphold this. It is intuitive, or has arisen as a design requirement from our research.
- **Leaning**: we think it might be something we should uphold, is currently upheld by wip, or is something we know we want but don't know is possible.
- **Open**: Actively trying to figure it out

We need a flexible and dynamic visual layer that the human can see and interact with, a simple and extremely dynamic object model that allows us to represent the vast array of things present in or on a computer, and some sort of authority layer that manages permissions for everything in the system. JEFF talks to all three layers, requesting permissions, manipulating the visualization, and editing and minting objects. JEFF may supervise other agents who handle tasks within the system. Multiple users should be able to collaborate in the same space effectively, without overwriting each other's work. In order to maximally facilitate ease of modification and creation, agora should whenever possible be composed of one substrate. The system should make it easy to improve itself, providing simple paths for friction and wishes to make their way into the world.

**Commitments**: 
*Strong*
- Agora will stay usable far into the future, even as it grows exponentially and covers the full range of applications.
- Simple or routine changes should not require writing complex shell code or JavaScript
- Verbs and operators should be reusable, so existing behavior and code can be applied to new situations and objects.
- The vocabulary for building views and behavior can keep growing without the system getting heavier
- Several people and agents can work on the same thing at once without breaking it or losing each other's work.
-  Anything you point at stays pointed at. Renaming, moving or reorganizing never silently breaks a link, a view or a comment.
- Usage of the Dynamic Desk should make subsequent edits faster, simpler, and more intuitive for JEFF and the user.  
- Each new capability costs less than the one before.
- The tools needed to navigate the desk, make changes, and understand the entire system should be fully accessible from within the desk. 
- JEFF should be able to make the full range of objects and applications that present on a normal computer using his basic toolset, though complex graphics like videogames and renderers remain out of scope. 
*Leaning*
- Data keeps its meaning after the program that made it is gone.
- There is one language to learn, and it applies everywhere
*Open*
- Are different verbs used at different levels of the system like system, visual, and object? 
- How do native applications run alongside? 
### Objects and Aspects
An Object (also called a referent) is similar to a file, but rather than being a rigid format, it hosts a collection of data, tags, and types known as aspects. Objects should be able to link to other objects, grow and change, and represent anything on the desk, including libraries and code objects.  Objects are the ultimate flexible interface for the future, something that can get built on top of for decades to come without getting cluttered, complicated, or restrictive.

**Commitments:** 
*Strong*
- One object can appear in many places, and it's the same object in all of them. Change it anywhere and it changes everywhere.
- A thing's identity is never reused and survives renames, moves and forks. 
- Anything you want to point at, comment on or link to (a datapoint, one day of a plan, a paragraph) can become addressable, without everything having to be.
- There should be a way to identify objects as they move between worlds.
- Some aspects are public and some are private, some objects are public and some are private.
*Leaning*
- Nothing goes silently stale.
- A value that depends on another either follows it or says plainly that it has stopped following.
- A copy is a new thing that remembers where it came from.
*Open*
- How do many users operate on the same data at the same time?
- How do we allow concurrent edits on different parts of a document to compose?
### Verbs and capabilities
Verbs are the basic structure of language, and using things like flip, tile, and replace should be natural, first class operations within agora. We are attempting to replace rigid JSON tool calls and JavaScript with intuitive verb-based operation on the desk, rather than one fixed rule set. 

*Held*
- Verbs should be learned once, and used anywhere where they apply, ideally with the same underlying implementation under similar action (ie dragging a window vs dragging a text box).
- Entering a space should describe what is available there.
- The rule set should grow and expand dynamically as new use cases are created. 
- It should be easy to mint new useful verbs from within the desk
- New verbs should whenever possible enter the world through the world as libraries of existing words.

*Leaning* 
- Entering a space should show its relevant verbs
- Before making a change you know everything it will affect.
- A change made of many steps should be able to partially succeed if there are good recovery paths, otherwise the change should apply all or nothing.
### Appearances and Visualization
The desk should at minimum implement and be able to represent all the functions and views of a normal desktop, though it may have more variable and flexible options for layouts, tiling, overlays, and transitions making it feel unique. Applications should be broadly customizable in appearance, layout, and composition. With the default being the addition and subtraction of visible tools and menus. Skinning your applications should be common, with many people choosing to fully customize the appearances over applications. In order to facilitate this, the view architecture needs to be adaptable and codable, while sharing a common contract about how it manipulates and and creates objects on the device. Agora also seeks to create composable views and as many live features as possible, with a graph embedded in a document updating in real time, or a weather chart updating in response to real weather regardless of whether its in a document or on the desktop wallpaper. 

*Held*
- Every view is fully able to be restyled, rearranged, copied, or replaced like every other thing
- The visualization machinery can grow, but it must not grow linearly with every new thing we want to draw.
- Views of things outside the world (the weather) stay current and say how fresh they are.
*Leaning*
- New things to show don't need new code in the core; what's specific to an app lives with the app.
- Native applications should share a similar style at default
*Open*
- Transitions and animations? 
- How do we compose views?
- What does the desktop look like (tiled windows, layered windows, no windows at all?)
### Scripting
In order to make easier the process of further development and complex features, the text based world should have a rich, native scripting language. It should be extremely extensible, just like Minecraft Redstone enables the building of a full computer inside Minecraft, or people made a computer inside LambdaMOO. Not saying it needs to make a computer, but it needs to be able to do basically anything with objects and appearances. 

*Held*
- Any program or application in Agora should be readable and transparent
- JEFF and the user perceive a shared state.
*Leaning*
- The language the terminal uses, the one that builds views, and the one that behavior is written in are all the same
*Open*
- What is the terminal interface? What are the important requirements and limitations our language needs for long term growth, stability, and security? 

## Default Applications
*Tentative*

- To Do
- Map
- Calendar / Mail
- Social
- Word Processor
- E-reader?
- AI
- File Manager / Viewer
- Code Editor
- Whiteboard / idea space
- Language learning
- Job Board
- Ticket manager / wallet?
## How the interface is composed

### Desktop and shell
The desktop and shell should be managed by some sort of always running process that makes sure things are composing properly, it is rarely edited by JEFF, though maybe in the future more changes are made to this layer as JEFF grows more powerful and embodied within the system. This layer should manage things like the task bar, system notifications, system wide search, and any other system wide features. It may manage the conversation with JEFF and the desk harness backend.

*Leaning*
- The shell is as changeable as anything else (bar dock and windows should be reshapable)
- There is always a way back when something breaks. Something independent can restore and recover even when the whole thing is made of changeable parts. 
### Applications and their views

Applications are the meat of the user experience, and they own appearances and views, but not objects. They may create and destroy objects, but objects are owned by the system, and each application must have some sort of permissions that allow it to modify the objects its using. Things like zoom, scroll state, and saves are personal state, and should not clutter history or overwrite someone else's personal state.

*Open*
- What is the appearance, view, lens, occurrence separation? How do those words serve us, overlap, and become unnecessary.

![[Pasted image 20260923162848.png]]

## Creating and changing capabilities

Ideally changes should be previewed directly onto the running desk itself, unless they are extremely complex. Changes should be able to be made to the running desk by JEFF without requiring a restart, refresh, or redownload. New capabilities should immediately be ready to be used by JEFF and the user without interfering with current work. 

*Held*
- Live preview and changes without restart
- New capabilities don't interrupt current work

*Open*:
- How are changes previewed and adopted? 
- How do useful capabilities and tools from others get adopted into the system?

## Log and Parallel Work

The desk's organization should be preserved so when you return it looks the same. Undo should be able to undo basically any event, though some events can not be rolled back and should be marked as such in the log. 

*Held*
- Almost anything can be undone
- Desk holds state
- No ones change silently overwrites someone else's
- Never blocked on an unrelated change
- Undo and replay restore what was recorded; they never re-send a message, re-run a program or repeat an effect outside the desk.

*Leaning*
- Merging across complex changes, keeping what doesn't conflict
- Offline use

## Authority and responsibility

*Held*
- Claims never grant themselves
- Every act has an author

**Open:**
- Who can change what?
- Which boundaries must remain independently enforceable?
- How do native operations relate to external systems?
## Biggest Challenges

Once we have a strong foundation, figuring out how to get visual changes and style comparable to normal applications. 

Making our substrate so good that it will last for decades of experimentation and building

Setting ourselves up so multiple people can build software together.

## Related documents

- [[Agora]]
- [[Current Implementation]]
- [[Previous Work]]
