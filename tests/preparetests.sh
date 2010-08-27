#!/bin/bash

cd ..

# Create that environment...

. env/bin/activate

for proj in common client server
do
    python setup.py develop
done
