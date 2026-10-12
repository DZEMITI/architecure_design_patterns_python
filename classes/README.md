<div style="display: flex; align-items: center; gap: 20px;">
  <img src="LogoWSEI.png" alt="Akademia WSEI" width="150">
  <div>
    <h1 style="margin: 0;">Information technology and design patterns - Labs</h1>
    <p style="margin: 6px 0 0;">Created by: mgr inż. Bartłomiej Cis</p>
  </div>
</div>

# Classes

Seven meetings. The first is an introduction to the app as it is. The next five are partial refactors, each using only the patterns listed for that meeting. The last meeting is a shared review.

The end-to-end test is the contract for every refactor. Run it from the project root after each change:

```bash
source .venv/bin/activate
python -m unittest test_e2e.py -v
```

Update the architecture diagram in the main README when a responsibility moves out of a handler.

| Class | Subject | Patterns |
|---|---|---|
| [1](01-introduction/README.md) | Introduction | theory of the patterns below |
| [2](02-decorator/README.md) | Request timing | Decorator |
| [3](03-factory-method-and-builder/README.md) | Records the app builds | Factory Method, Builder. Singleton as a critique |
| [4](04-adapter-and-facade/README.md) | The macros service and diet targets | Adapter, Facade |
| [5](05-strategy-state-and-command/README.md) | Periods, the weekly goal, log and undo | Strategy, State, Command |
| [6](06-observer/README.md) | Reactions after a session is logged | Observer. Composite and Proxy as a decision |
| [7](07-review/README.md) | Shared review | compare the solutions |

These patterns are left out of the required work: Prototype, Bridge, Iterator, Mediator, Visitor, Abstract Factory, and a second pass over Singleton or Observer. The app has no clones, no parallel hierarchy, no custom collection to walk, no object that coordinates the others, and no structure that needs a new operation on every element. Abstract Factory would only repeat Factory Method with a second product family this app does not have.
