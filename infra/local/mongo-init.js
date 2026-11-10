// Root bootstrap only. Application credentials have access to this synthetic DB.
const credentials = JSON.parse(
  require("fs").readFileSync("/run/shipsense/mongo-app.json", "utf8"),
);
db.getSiblingDB("shipsense_fixture_p01").createUser({
  user: credentials.user,
  pwd: credentials.pwd,
  roles: [{ role: "readWrite", db: "shipsense_fixture_p01" }],
});
