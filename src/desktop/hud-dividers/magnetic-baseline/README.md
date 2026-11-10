# Captured main fixtures

These two JavaScript files are inert differential-test inputs from main
09ef2530ec848cbbcf0afc5d0934737095c3cc69:

- partition.js: git blob 32d23e950a32456edad5713d612536ade67f92c8
- partition-ui.js: git blob e0007181d477cb4303d752df94bf7173e89b6444

Verified with git hash-object against git rev-parse of those main paths.
test_magnetic_optout.js evaluates them inside disposable DOM-double VMs.
They are not served, launched or loaded by the painter.
