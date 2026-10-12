<div style="display: flex; align-items: center; gap: 20px;">
  <img src="../LogoWSEI.png" alt="Akademia WSEI" width="150">
  <div>
    <h1 style="margin: 0;">Information technology and design patterns - Labs</h1>
    <p style="margin: 6px 0 0;">Created by: mgr inż. Bartłomiej Cis</p>
  </div>
</div>

# Class 7 — Shared review

No new pattern. Each group shows what it changed and defends what it left alone.

## How to explain a pattern you used

When you name a pattern in the review, give four parts. The class README for that pattern is the source.

- **Intent.** One sentence on the job, such as "add timing around every route without editing the routes" or "translate the macros service into lifestyle names".
- **Roles.** Which type or function is the subject, the wrapper, the creator, the strategy, the command, or the listener. A pattern with no object playing the role is a renamed function.
- **Collaboration.** Who calls whom, and what is true before the call returns. For a decorator, the wrapped function still returns the HTTP response. For an observer, the log row is already stored before `update` runs.
- **Boundary.** What this pattern is allowed to change. Undo's command changes the log file and leaves notices alone. The adapter changes names and transport, and leaves the lifestyle choice to the facade.

## What each group brings

- The architecture diagram after class 6, and the diagram from class 1 if you still have it.
- The list of patterns you actually used, each with the file or type that plays that role.
- One place where two groups could apply the same pattern differently. For example, the builder on the calories response or on the targets response, or the proxy in front of the macros adapter.
- One change you considered and did not make, with the reason. Composite is a likely example.
- The result of `python -m unittest test_e2e.py -v` on the code you are showing.

## Discussion

Walk one request, `POST /log` of a 30 minute run, across the refactored code. Name the decorator, the factory, the command, the state, and the observers as the call passes them. Then walk `GET /targets` for a week and name the facade, the period strategy, and the adapter.

Compare the lifestyle result. A week that burns 487 kcal is still `not active` / `sedentary` in the tests, because the lifestyle table is total energy and the logs are exercise only. Discuss whether that rule should change, and what would have to change in the tests and the table together. Do not treat a passing test as proof that the rule matches the outside world.

Close on these questions:

- Which pattern removed a real copy, and which one mostly renamed a function?
- What would break first if a second user profile had to be stored?
- Which behavior is safe to change only when the tests change with it?

## Done when

Every group has shown a diagram, accounted for the patterns from classes 2 to 6, and described one design choice it is willing to keep.

## Report

Each student writes a PDF and uploads it to the course section on the [WSEI e-learning platform](https://dl.wsei.pl/course/section.php?id=2220).

The PDF contains:

- Your name.
- A written explanation of what you did in this class.
- A screenshot of the architecture diagram in the main `README.md`, as it stands at the end of this class. The diagram is a Mermaid flowchart. Syntax is in the [Mermaid flowchart guide](https://mermaid.ai/open-source/syntax/flowchart.html).
- The link to your own repository with this class's commits pushed, for example `https://github.com/YOUR_USER/architecure_design_patterns_python`.