# Collective Project 001

## Description

This is a collective project with contribution from any member of the open-source communities, and in particularly a huge contribution from the OD3E community ( https://o3de.org/ ) providing the main character of this project, `Odie`.

## Primary Goal

We aim at creating a short-story with a single character `Odie` in a still-to-be-defined situation, with a collective effort by members of various open-source communities.

And we are going to render the results in a offline mode (via `usdrecord` and a non-yet-specified render-delegate, probably Pixar's `Storm` available with `OpenUSD`).

The resulting OpenUSD files will be avaiable in the OpenUSD Assets sub-workinggroup (wg-usd-assets).

## Secondary Goals

Ideally, we want the final shot to be able to render also in realtime in O3DE and/or any other realtime renderer.

And we want to provide deliverables in other formats like live-skinning-character Odie and all the dcc/app files (working files) utilized to create OpenUSD fragments to contribute to the final shot.

We aim at having the entire set of files of every goal (source/working files, OpenUSD deliverables, etc) in the `DPEL` library ( https://dpel.aswf.io/ ).

## O3DE Community

This project is centered around the asset `Odie`, generiously offered by the O3DE community ( https://o3de.org/ ).

Original file and licenses can be found here: https://github.com/o3de/odie-3d-assets/tree/main

## OpenUSD Community

The main deliverable will be a set of `OpenUSD` files for the assets, cameras, lights, and all the elements of the short, in a renderable-state, to be able to be loaded in `usdview` or `usdrecord` for generating final images.

We want to leverage `OpenUSD`'s composition arcs to enable non-destructive workflows, as it would happen in a proper VFX Pipeline, with well defined tasks and deliverables that compose together in the renderable shot file.

The asset-structure is a variation of the original structure provided by the OpenUSD Assets WorkingGroup (wg-usd-assets), 

## Version tracking

We are going to be using `git` as main "version tracker", assuming with are always on the latest version, and previous versions are just older commits in the main repo.

The various `CHANGELOG` files in each asset/shot folder will function as publishing-version-history.

## Pipeline

The `pipeline` is made of `python` scripts to be able to, for example, validate or render turntables of published assets.

We are hoping to connect with the `wg-ci` Working group on the Academy Software Foundation slack, and connect some scripts more automatically happening when updates are pushed to the repo (TBD).




