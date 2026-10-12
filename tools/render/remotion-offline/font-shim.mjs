// Offline stand-in for @remotion/google-fonts (sandbox cannot reach fonts.gstatic.com).
// Returns the same shape; uses system font stacks instead of downloading.
const stack = (name) => `"${name}", "DejaVu Sans", "Liberation Sans", sans-serif`;
export const loadFont = (style = 'normal', opts = {}) => ({
  fontFamily: stack('Space Grotesk'),
  fontStyle: style,
  waitUntilDone: async () => {},
  fontFamilyStack: stack('Space Grotesk'),
});
export default { loadFont };
