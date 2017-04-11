#!/bin/bash

py.test --cov-config .coveragerc --cov=anitya --cov-report term \
    --cov-report xml --cov-report html $*
