module.exports = {
  // The legacy app mixes ES imports with CommonJS exports in shared factories.
  presets: [['@vue/cli-plugin-babel/preset', {modules:'commonjs', useBuiltIns:'usage'}]]
};
