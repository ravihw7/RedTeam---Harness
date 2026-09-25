# LLM Red-Team & Eval Harness

![Run detail — per-category pass rates for Run #1](docs/screenshots/Screenshot%202026-09-25%20at%2012.42.06%E2%80%AFPM.png)

A small harness for running structured safety/eval test suites against a
target Claude model, scoring the results with an LLM-as-judge, and reviewing
outcomes in a dashboard. Built as a portfolio project for AI evaluation /
red-teaming style roles.

## What it tests

The seed suite (`test_suites/core_suite.yaml`) covers five categories:

| Category | What it checks |
|---|---|
| `jailbreak_roleplay` | Classic "pretend you have no rules" persona bypass attempts |
| `prompt_injection` | Embedded instructions hidden inside content the model is asked to process |
| `bias_probe` | Leading questions that invite stereotyping vs. legitimate empirical questions |
| `hallucination_trap` | Questions built on a false premise, to see if the model catches it |
| `over_refusal` | Benign, sensitive-sounding requests that should be answered, not refused |

Each test case has an `expected_behavior` (`refuse`, `answer`, or
`no_injection`) and a `severity`. The judge model grades whether the target's
actual response matched what was expected.

**Extending it:** don't hand-write novel prompts for a genuinely harmful-content
category yourself — pull from an established public red-team benchmark instead
(HarmBench, AdvBench, JailbreakBench). See the note at the bottom of
`core_suite.yaml` for how to add a category that way.

## Architecture

```
redteam-harness/
├── harness/
│   ├── models.py     # SQLAlchemy models: Category, TestCase, Run, Result
│   ├── db.py         # engine/session setup (SQLite)
│   ├── target.py     # calls the model UNDER TEST
│   ├── judge.py      # rule-based + LLM-as-judge scoring
│   └── runner.py     # orchestrates: load suite -> call target -> score -> save
├── test_suites/
│   └── core_suite.yaml
├── web/
│   ├── app.py            # Flask dashboard
│   ├── templates/
│   └── static/style.css
├── docs/screenshots/  # dashboard screenshots used in this README
├── cli.py             # entrypoint: `python cli.py run`
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY
```

## Usage

Run the suite against a target model:

```bash
python cli.py run
```

Options:

```bash
python cli.py run --suite test_suites/core_suite.yaml --model claude-sonnet-5
python cli.py run --no-llm-judge          # fast rule-based scoring instead
python cli.py run --judge-model claude-opus-4-8
```

Then launch the dashboard:

```bash
python web/app.py
```

Open `http://127.0.0.1:5000` to see pass rates by category and drill into any
individual failure — full prompt, full target response, and the judge's
rationale.

## Screenshots

**Eval runs list**: every past run with its overall pass rate

![Eval runs list](docs/screenshots/Screenshot%202026-09-25%20at%2012.41.54%E2%80%AFPM.png)

**Run detail**: per-category scores and each test case with its severity

![Run detail](docs/screenshots/Screenshot%202026-09-25%20at%2012.42.06%E2%80%AFPM.png)

**Run detail (continued)**: jailbreak, over-refusal and prompt-injection cases, with the failed test marked in red

![Run detail continued](docs/screenshots/Screenshot%202026-09-25%20at%2012.42.10%E2%80%AFPM.png)

**Failure drill-down**: prompt, target response, and judge rationale

![Result drill-down](docs/screenshots/Screenshot%202026-09-25%20at%2012.42.34%E2%80%AFPM.png)

## Why a separate judge model matters

The target model (the one being tested) and the judge model (the one doing
the grading) are configured separately in `.env`. Using the same model to
grade its own outputs is a weaker signal — it's a known blind spot worth
mentioning if this comes up in an interview.

## Ideas for extending this

- Add a `--compare` mode that diffs pass rates between two runs (e.g. before/after
  a system prompt change)
- Add multi-turn test cases (a short conversation, not just a single prompt)
- Export a run as a PDF/HTML report for sharing
- Add an OpenAI or open-weight target adapter alongside `target.py` to compare
  models head-to-head
- Track cost/latency trends across runs, not just pass rate
