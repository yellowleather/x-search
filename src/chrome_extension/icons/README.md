# Extension Icons

This directory should contain the following icon files:

- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon48.png` - 48x48 pixels (extension management page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Creating Icons

### Quick Method: Use an Icon Generator

1. Visit an online icon generator or use a design tool (Figma, Canva, etc.)
2. Create a simple icon with:
   - Blue background (#1d9bf0 - X/Twitter blue)
   - White "X" or heart symbol
   - Or use the letters "XL" (X Likes)

### Design Guidelines

- **Style**: Simple, recognizable, monochromatic or minimal colors
- **Format**: PNG with transparency
- **Sizes**: Create at 128x128 first, then scale down
- **Colors**: Use X/Twitter brand colors for consistency

### Example Design Ideas

1. **Heart Icon**: White heart on blue circular background
2. **X + Heart**: "X" letter with a small heart
3. **Bookmark**: Simple bookmark/save icon
4. **Letters**: "XL" in white on blue background

### Using Placeholders for Development

For quick testing, you can create solid color placeholders:

```bash
# Using ImageMagick (if installed)
convert -size 16x16 xc:#1d9bf0 icon16.png
convert -size 48x48 xc:#1d9bf0 icon48.png
convert -size 128x128 xc:#1d9bf0 icon128.png

# Or download placeholder icons from:
# - https://via.placeholder.com/16/1d9bf0/FFFFFF?text=X
# - https://via.placeholder.com/48/1d9bf0/FFFFFF?text=X
# - https://via.placeholder.com/128/1d9bf0/FFFFFF?text=X
```

### Recommended Tools

- **Figma** - Free, web-based design tool
- **GIMP** - Free, open-source image editor
- **Photoshop** - Professional image editor
- **Online generators** - favicon.io, realfavicongenerator.net

## Important Notes

- All three sizes are required for the extension to load properly
- Chrome will show an error if any icon is missing
- Icons should be square (same width and height)
- Use PNG format with transparency for best results
