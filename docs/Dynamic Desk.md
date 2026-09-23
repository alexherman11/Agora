> A system should be built with a minimum set of unchangeable parts; those parts should be as general as possible; and all parts of the system should be held in a uniform framework.
>
> If a system is to serve the creative spirit, it must be entirely comprehensible to a single individual.
>
> — Daniel H. H. Ingalls, *[Design Principles Behind Smalltalk](https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html)* (1981)

## The current design in one page
In order to maximally facilitate ease of modification and creation, agora should whenever possible be composed of one substrate. The object and facet model is a *tentative attempt* to tackle that challenge.

We need a flexible and dynamic visual layer that the human can see and interact with, a simple and extremely dynamic object model that allows us to represent the vast array of things present in or on a computer, and some sort of authority layer that manages permissions for everything in the system. JEFF talks to all three layers, requesting permissions, manipulating the screen, and editing and minting objects. There should exist a bridge between the object and the appearance layer, so that routine changes to objects do not require complex visual orchestration. Likewise, verbs or operators should be reusable, so that implementing dragging or tiling behavior is only done once or rarely, rather than every time a new application is made. 

> Usage of the Dynamic Desk should make subsequent edits faster, simpler, and more intuitive for JEFF and the user. 

The structure that JEFF uses to navigate the desk is based on a text adventure game, with commands like `help` and `examine` being used frequently to navigate and place objects in the desk. JEFF should be able to make the full range of objects and applications that present on a normal computer using his basic toolset, though complex graphics like videogames and renderers remain out of scope. 

**Open:** Is the object / facet model the optimal model for extensibility and malleability? What is the bridge architecture between objects and appearances? What verbs are used? Are different verbs used at different levels of the system like system, visual, and object? How are these layers moved between? How do native applications run alongside? 
### Objects and relationships
An Object is similar to a file, but rather than being a rigid format, it can be a collection of multiple data types together which form some sort of kind. Various data types or attributes can be attributed to the objects and these are knows as facets. Objects should be able to link to other objects, grow and change, and represent useful pieces of information on the desktop, as well as whatever is wanted to be represented. Think of Objects as the ultimate flexible interface, something that can get built on top of for decades to come without getting cluttered, complicated, or lacking in opportunities for novel development. Objects should be a framework that allow things to be built that we can't even begin to imagine.

Objects should be openable in multiple places at once. Modifying the document in one view should modify it in the other. Certain objects will be conditional on other objects. 

**Open:** What is the best object model, and how does it connect to the text based desk JEFF can interact with? At what level of abstraction do objects get their own representation (should datapoints on a graph be objects too?) How do objects compose to form more complex things?
### Verbs and capabilities
Verbs are the basic structure of language, and using things like flip, tile, and replace should be natural, first class operations within agora. We are attempting to replace rigid JSON with more flexible tool calls that allow for intuitive operation of the desk, rather than one fixed rule set. Additionally, the rule set should be adaptive and discoverable. When examining an object, only verbs usable on that object should be seen, and when entering a new layer or space, relevant verbs for that space should become visible. When possible, the implementation of verbs should be consistent, both in behavior and in code, making the system light and intuitive. A capability is reusable if calling the same verb on two different types of objects, (or an object and an appearance etc), produces the same kind of behavior, ideally with the same code implementing the change both times. 
### Appearances and Visualization
The desk should at minimum implement and be able to represent all the functions and views of a normal desktop, though it may have more variable and flexible options for layouts, tiling, overlays, and transitions making it feel unique. Applications should be broadly customizable in appearance, layout, and composition. With the default being the addition and subtraction of visible tools and menus. Skinning your applications should be common, with many people choosing to fully customize the appearances over applications. In order to facilitate this, the view architecture needs to be adaptable and codable, while sharing a common contract about how it manipulates and and creates objects on the device. 

Agora also seeks to create composable views and as many live features as possible, with a graph embedded in a document updating in real time, or a weather chart updating in response to real weather regardless of whether its in a document or on the desktop wallpaper. 

### Scripting
In order to make easier the process of further development and complex features, the text based world should have a rich, native scripting language. It should be extremely extensible, just like Minecraft Redstone enables the building of a full computer inside Minecraft, or people made a computer inside LambdaMOO. Not saying it needs to make a computer, but it needs to be able to do basically anything with objects and appearances. 

**Open:** Is this the language the terminal uses? Does the terminal look like jeff's interface? What is the scripting language?
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
### Applications and their views
- What do applications own?
- What machinery should they share?

Applications are the meat of the user experience, and they own appearances and views, but not objects. They may create and destroy objects, but objects are owned by the system, and each application must have some sort of permissions that allow it to modify the objects its using. Appearances are an inital idea for how each application will be rendered, it is the set of code that runs to generate the fonts, colors, and organization of objects. An instance of an appearance could be a view that holds things like zoom, scroll state, and saves. 

**Open:** Most of the appearance view separation

### The visual bridge

**Open:**
- How does object state become a usable interface?
- What updates automatically?
- When is new code actually necessary?
## Creating and changing capabilities

Ideally changes should be previewed directly onto the running desk itself, unless they are extremely complex. Changes should be able to be made to the running desk by JEFF without requiring a restart, refresh, or redownload. This may involve the decomposition of servers running Agora, though a more elegant solution would be preferred. New capabilities should immediately be ready to be used by JEFF and the user without interfering with current work. 

**Open:**
- How are definitions, rules, components, and programs authored?
- How are changes previewed and adopted? 
- How do we preserve ongoing work?
- How do useful capabilities get reused?

## State, change, and continuity

The desk's organization should be preserved so when you return it looks the same. Undo should be able to undo basically any event, though some events can not be rolled back and should be marked as such in the log. 

**Open:**
- How are concurrent changes handled?

## Authority and responsibility

**Open:**
- Who can change what?
- Which boundaries must remain independently enforceable?
- How do native operations relate to external systems?

## Important choices and their reasons

- What approach are we taking?
- Why?
- What alternatives did we consider?
- What would make us reconsider?
## Open design questions

- What needs an experiment?
- What can remain unspecified for now?
## Related documents

- [[Agora]]
- [[Current Implementation]]
- [[Previous Work]]
