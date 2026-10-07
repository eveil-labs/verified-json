# Lean submission tooling assessment

Planning observations, 2026-10-07. No tools were installed, built, executed, or qualified in this study. Browser views can represent different cached revisions. Before adoption, retrieve every required file from one immutable source commit and record its identity. “Written in Lean” does not mean the verifier, its orchestration, sandbox, or exported-input parser has itself been formally verified.

## Recommended choice

Reuse the **trusted challenge / untrusted submission / generated solution bridge** design from lean-eval and comparator. Adapt a narrow audited checker/generator slice rather than importing the complete benchmark catalog or its unrelated dependencies. Add explicit resource/verdict handling, worker lifetime containment, sealed artifacts, minimal allowed imports, and runtime correspondence checks for implementation tickets. SafeVerify can supply useful supplemental comparisons and diagnostics, but is not a replacement for the comparator boundary or a qualified independent kernel.

## Current public observations

| Tool | Useful capability | Material limit | Candidate role |
| --- | --- | --- | --- |
| [leanprover/lean-eval](https://github.com/leanprover/lean-eval) | Maintainer-authored targets, generated participant workspaces, multi-file submissions, explicit theorem/definition holes, protected bridge/configuration, pinned external tools; its workspace test requires nanoda. | A benchmark and integration system, not a proof about its own machinery. The complete repository includes unrelated mathematical catalogs and dependencies. | Reuse its ticket/workspace boundary and selected generator/test components. |
| [leanprover/comparator](https://github.com/leanprover/comparator) | Exports challenge/solution environments, checks exact target declarations and transitively referenced constants, audits permitted axioms, and replays the solution through Lean and optional external kernels. | Requires trusted challenges/dependency closure and a correct sandbox. Definition holes require additional specification review. Stock process errors do not provide our proposed precise PASS/REJECT/INFRA policy. | Primary verification engine after pin-specific qualification and containment fixes. |
| [GasStationManager/SafeVerify](https://github.com/GasStationManager/SafeVerify) | Same-kernel environment replay; declaration kind/type/body checks; transitive axiom collection. | README says it does not replay imports and does not provide compilation sandbox or runtime-attribute checking. Definitions transitively depending on a target `sorry` may be treated as mutable. | Supplemental diagnostic or narrow audited adaptation, not sole release gate. |
| [lean4export](https://github.com/leanprover/lean4export) | Produces the serialized declaration closure used by comparator and independent checkers. | Reading potentially adversarial `.olean` files is itself an unsafe-input boundary. It must match the selected compiler's object format and run in a contained worker. | Pin, build, qualify, and isolate its exact compatible version. |
| Lean kernel replay / lean4checker | Checks compiled proof declarations again rather than trusting elaboration's state. | Same kernel implementation is not an independent implementation; directly reading malformed `.olean` files needs isolation. Imported closure handling differs by flags/tool version. | Mandatory native replay layer through a supported qualified interface. |
| nanoda or another independent checker | Additional independently implemented proof checking over exported input. | Supported features, accepted axiom basis, primitive definitions, special reductions, and input version must match the actual project footprint. A decline or crash proves nothing about the candidate. | Mandatory supported independent layer, selected by measured qualification. |
| [Lean Kernel Arena](https://github.com/leanprover/lean-kernel-arena) | Standardized accept/reject/corner/performance cases and checker configurations help test the chosen kernels. | The arena assumes good faith and explicitly does not sandbox checkers. Its rankings and tests do not certify our target closure or containment. | Source of pinned negative/positive canaries; do not directly execute arbitrary arena checker submissions on a privileged host. |

The official proof-validation guidance recommends trusted statement comparison, sandboxed elaboration, serialized export, and external checking for adversarial submissions. It retains explicit assumptions about statement meaning, plumbing, sandbox, and simultaneous checker bugs. [Validating a Lean Proof](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

## Version and footprint qualification

The visible official release list identifies **4.35.0-rc4** as a prerelease and **4.34.1** as latest stable. The user has explicitly requested newest Lean including RCs for the standalone project; the candidate target is therefore exact `leanprover/lean4:v4.35.0-rc4`, subject to a qualified complete verifier envelope. Existing releases and individual tickets use exact pins, never a moving `latest` selector. [Official releases](https://github.com/leanprover/lean4/releases)

Observed version surfaces differ:

- lean-eval's visible toolchain is **4.35.0-rc3**. Its SECURITY pin table names comparator `d03acab154d269c06e60e4de7e4cc85deebff94b`, exporter `076e8e57707e813375e8f9da8bf989799ace9680`, landrun `5ed4a3db3a4ad930d577215c6b9abaa19df7f99f`, and nanoda fork `68d5ca9db226849b41a6fff59d796ff19d0a8840`. These are research leads; do not assume those binaries can read rc4 objects. [Toolchain](https://raw.githubusercontent.com/leanprover/lean-eval/main/lean-toolchain), [pin policy](https://github.com/leanprover/lean-eval/blob/main/SECURITY.md)
- comparator's visible **master** toolchain names **4.35.0-rc4**. That is different from the comparator commit in the lean-eval pin table. A version declaration is not an executed compatibility result. [Comparator toolchain](https://github.com/leanprover/comparator/blob/master/lean-toolchain)
- SafeVerify's visible toolchain page names **4.27.0**. Its README documents historical backport branches. Do not claim rc4 compatibility without a fresh audited port/build and checker tests. [SafeVerify toolchain](https://github.com/GasStationManager/SafeVerify/blob/main/lean-toolchain)
- FloatLib's previously inspected surfaces name **4.34.0**. Its narrow binary64 dependency slice requires rc4 compatibility qualification and any necessary small pinned patch; unrelated numerical modules remain outside the shipping/parser closure. This is separate from the larger footprint of tools needed to elaborate tactics.

Qualify the selected compiler, exporter, comparator, sandbox/supervisor, native replay, independent kernel, generator, and numeric-module closure as one envelope. The verifier's extra Lean/meta dependencies need not be production JSON runtime dependencies. Proof-generation tactic imports are separately inventoried from imported production modules and runtime function reachability.

## Important upstream limitations to address

At its documented pin, lean-eval acknowledges a writable-`.lake` race: a surviving untrusted descendant could modify artifacts before export. It also records definition-hole underconstraint and a nanoda string-handling caveat. These are known qualifications of the browsed integration, not a demonstrated exploit against this new project. [lean-eval security model](https://github.com/leanprover/lean-eval/blob/main/SECURITY.md)

Comparator [issue 77](https://github.com/leanprover/comparator/issues/77) and proposed [PR 78](https://github.com/leanprover/comparator/pull/78) address descendant containment. The PR is visibly open, targets another branch, and describes namespace-based cleanup with a fail-closed setting. Do not treat it as an adopted master fix. A project may instead put the whole untrusted build/export inside a supervisor-controlled ephemeral VM/container with verified descendant teardown and artifact sealing. This wrapper requires its own real canaries; mere container branding is insufficient.

Current comparator master `Main.lean` constructs landrun arguments with best-effort behavior, a broad readable filesystem, and writable build outputs. Its external-checker branch reports a nonzero process exit as rejection and catches invocation failures in the same result family. A project wrapper must preserve specific failure causes and enforce missing containment/checker compatibility as INFRA, never as a proof verdict. Do not blindly inherit the defaults. [Comparator orchestration](https://raw.githubusercontent.com/leanprover/comparator/master/Main.lean)

The current comparator README also calls for an address-family restriction around invocation for a sandbox concern. Reassess all required OS controls from the adopted exact commit rather than copying a command from a mutable README. [Comparator README](https://raw.githubusercontent.com/leanprover/comparator/master/README.md)

## What target comparison actually establishes

Comparator's `compareAt` checks target name/kind/type/universe metadata and follows referenced constant information. Explicit definition-hole targets compare their types and safety levels rather than implementation bodies. This makes a reviewed total contract essential for implementation tickets; “this function has the right type” is not its behavior proof. [Compare.lean](https://raw.githubusercontent.com/leanprover/comparator/master/Comparator/Compare.lean)

Its axiom checker walks selected theorem and definition targets transitively and restricts reachable axiom names. Our wrapper must enumerate all required roots and separately audit all submitted/shipping declarations, so an incomplete unused helper cannot accidentally become tomorrow's public dependency. [Axioms.lean](https://raw.githubusercontent.com/leanprover/comparator/master/Comparator/Axioms.lean)

SafeVerify's README allows a definition's body to change if the target depends on `sorry`, including transitively. Its visible source defaults `disallowPartial` to the presence of `--disallow-partial`, rejects unsafe module constants, and exempts a named compiler recursion shim from that partial check. These observed behaviors need pin-specific tests; they are not our project policy. We should use an explicit maintainer-owned mutable-declaration list instead of inferring mutability from placeholders. [README](https://github.com/GasStationManager/SafeVerify/blob/main/README.md), [Main.lean](https://github.com/GasStationManager/SafeVerify/blob/main/Main.lean)

## Native evaluation and runtime correspondence

The official reference says native `decide`/`bv_decide` computations add dedicated axioms on current Lean, and that the old `Lean.trustCompiler` machinery was removed in 4.35. A keyword scan for that old name therefore cannot establish safety. Our default is the exact transitive maximum allowlist `{propext, Quot.sound, Classical.choice}`, excluding native-evaluation axioms regardless of spelling. Kernel-reduced `decide` remains available when it constructs a normal checked proof. [Native evaluation guidance](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

`@[implemented_by]` can replace verified mathematical code with an unchecked runtime implementation; `@[extern]` adds a foreign implementation obligation. Their source and compiled-environment metadata require separate auditing. `@[csimp]` comes with an equality proof but its execution still uses the trusted compiler. No comparator result alone proves a binary faithful to its logical definition. [Lean implementation attributes](https://lean-lang.org/doc/api/Lean/Compiler/ImplementedByAttr.html)

## Qualification outcome required before opening proof tickets

The adoption ticket must deliver one exact source envelope, an audited minimal generator/checker adaptation, real sandbox and artifact-lifetime canaries, native/independent proof replay canaries, a portable structured verdict schema, and an integration test using at least one known good and several intentionally bad community submissions. Every advertised required layer must actually execute. No result from this planning study qualifies the machinery or authorizes running untrusted Lean on a maintainer's host.
