## Summary
What does this PR change and why?

## Related
Closes # (issue) / addresses audit finding (e.g. C2, H1).

## Validation
- [ ] `pytest tests/ -m "not slow"` passes
- [ ] `flake8` / `black --check` / `isort --check` pass
- [ ] If detection behaviour changed, benchmark re-run and numbers included
      below (false-positive rate on human text must not regress):

```
python -m src.evaluation.benchmark --analyzer ensemble
# paste Accuracy / F1 / AUROC / FPR / FNR / ECE here
```

## Notes for reviewers
Anything non-obvious, trade-offs, or follow-ups.
