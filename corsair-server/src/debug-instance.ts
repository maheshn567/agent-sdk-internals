import { corsair } from "./corsair.js";

console.log("telegram keys methods:", Object.getOwnPropertyNames(corsair.telegram.keys));
console.log("gmail keys methods:", Object.getOwnPropertyNames(corsair.gmail.keys));
console.log("github keys methods:", Object.getOwnPropertyNames(corsair.github.keys));

