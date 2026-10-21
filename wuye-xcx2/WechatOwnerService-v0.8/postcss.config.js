module.exports = {
  parser: require('postcss-comment'),
  // Inline imports before uni-app transforms units and component selectors.
  plugins: [require('postcss-import'), require('@dcloudio/vue-cli-plugin-uni/packages/postcss')]
};
