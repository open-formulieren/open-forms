# Mappings to solve with migrations

TODO: figure out backwards compatibility layer for people using stylesheets for their design token
overrides, rather than our admin interface.

-> CSS overrides with temporary, private variables? and mark those as breaking change in 3.0?

## Footer

**Colors**

- of.page-footer.bg -> utrecht.page-footer.background-color
- of.page-footer.fg -> utrecht.page-footer.color

**Responsive styles**

Note - shorthands will break here and require manual intervention - perhaps we shouldn't map those,
since the CSS itself is backwards compatible - instead document the upgrade steps.

- of.page-footer.mobile.padding ->
  of.utrecht-page-footer.mobile.padding{block-end,block-start,inline-end,inline-start}
- of.page-footer.tablet.padding ->
  of.utrecht-page-footer.tablet.padding{block-end,block-start,inline-end,inline-start}
- of.page-footer.laptop.padding ->
  of.utrecht-page-footer.laptop.padding{block-end,block-start,inline-end,inline-start}
- of.page-footer.desktop.padding ->
  of.utrecht-page-footer.desktop.padding{block-end,block-start,inline-end,inline-start}

## Header

**Colors**

- of.page-header.bg -> utrecht.page-header.background-color
- of.page-header.fg -> utrecht.page-header.color

**Responsive styles**

Note - shorthands will break here and require manual intervention - perhaps we shouldn't map those,
since the CSS itself is backwards compatible - instead document the upgrade steps.

- of.page-header.mobile.padding ->
  of.utrecht-page-header.mobile.padding{block-end,block-start,inline-end,inline-start}
- of.page-header.tablet.padding ->
  of.utrecht-page-header.tablet.padding{block-end,block-start,inline-end,inline-start}
- of.page-header.laptop.padding ->
  of.utrecht-page-header.laptop.padding{block-end,block-start,inline-end,inline-start}
- of.page-header.desktop.padding ->
  of.utrecht-page-header.desktop.padding{block-end,block-start,inline-end,inline-start}

- of.page-header.logo-return-url.min-height -> of.page-header.logo-return-url.min-block-size
- of.page-header.logo-return-url.min-width -> of.page-header.logo-return-url.min-inline-size
- of.page-header.logo-return-url.mobile.min-height ->
  of.page-header.logo-return-url.mobile.min-block-size
- of.page-header.logo-return-url.mobile.min-width ->
  of.page-header.logo-return-url.mobile.min-inline-size
