const express = require("express");
const bodyParser = require("body-parser");
const app = express();
const port = 3000;

// Middleware to parse form data
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files from the 'public' folder
app.use(express.static("public"));

// Handle form submission
app.post("/submit", (req, res) => {
  const formData = req.body;
  console.log("Form Data Received:", formData);
  res.send("Form successfully submitted!");
});

// Start the server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
