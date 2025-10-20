const fs = require('fs');
const path = require('path');

const packageJsonPath = path.join(__dirname, 'node_modules', 'node-pty', 'package.json');

if (fs.existsSync(packageJsonPath)) {
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    if (!packageJson.scripts) {
      packageJson.scripts = {};
    }

    packageJson.scripts.install = 'node-gyp rebuild --nodedir=/data/data/com.termux/files/usr/include/node';
    
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
    console.log('Successfully patched node-pty/package.json');
  } catch (error) {
    console.error('Failed to patch node-pty/package.json:', error);
    process.exit(1);
  }
} else {
  console.log('node-pty/package.json not found, skipping patch.');
}
