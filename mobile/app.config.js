// Permite nombrar la app al compilar (APP_NAME=Cafecín); sin la variable se llama Mesa7.
module.exports = ({ config }) => ({
  ...config,
  name: process.env.APP_NAME || config.name,
});
