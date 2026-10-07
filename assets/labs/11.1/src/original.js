// Original: a small license checker
function checkLicense(key) {
  var parts = key.split("-");
  if (parts.length !== 3) return false;
  var sum = 0;
  for (var i = 0; i < parts[0].length; i++) {
    sum += parts[0].charCodeAt(i);
  }
  return sum === 266 && parts[1] === "PRO" && parts[2].length === 4;
}
console.log(checkLicense("ABCD-PRO-2024"));
