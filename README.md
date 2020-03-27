## Pipenv

This project uses pipenv for the required packages! Simply type `pipenv install` to create a virtual environment and install all required packages within. (pipenv must be installed first!)

## Project as package

This project is designed as python package so it can easily included in other projects. Run `import ga_opf_pp` to use the package.

To run the example file, go to the parent directory and call
`python -m ga_opf_pp.examples`.

## Advantages and disadvantages to build-in pandapower OPF

### Advantages
- P and Q can be optimized separately
- Arbitrary objective functions possible (e.g. min(sum((u-1)^2)))
- Arbitrary constraints are easily to include (e.g. max apparent power)
- Tap-changer of transformer + switches + shunts can be optimized, too
- Constraints can (or rather must) be soft-constraints

### Disadvantages
- Far slower than pp-OPF
- More parameters (population size, mutation rate etc.) -> more effort for implementation
