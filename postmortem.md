# Post Mortem

## The good

We finished it! It was a great team effort!

We delivered a [short (low-res here)](collectiveproject001_final_lowres.mov).

Rendered with [Pixar&#39;s RenderMan](https://renderman.pixar.com/) (Thank you Pixar for a license!)

We made a gallery of various renderers rendering the render-purpose of a few important frames, [here](shots/s001_001/usdrecord_renders/README.md)

## The bad

- Project planning.
  - For our scope Slack and meetings worked well...but they were pushed to the limit.
- OpenPBR not yet supported in all renderers.
- Retargeting animation from proxy to render purposes.
- Normal mapping.
- Unable to test all the renderers we hoped for.

## The ugly

- MaterialX not fully supported by all renderers
- Reduced to a simple standard_surface to be able to render in Renderman
- ShapingAPI not supported by all renderers (see gallery)
- Default exposure issues
