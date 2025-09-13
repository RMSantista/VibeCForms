# Roadmap

## Upcoming adjustments and new features:

- Make the form generator dynamic, allowing it to read fields from a file. This way, when running the program, the form will read this document and create the respective fields as specified. This will allow any type of form to be generated automatically, simply by redefining the fields in the file.

- Separate the program into functional layers, splitting layout and validation rules from the main program file.

- Create connection and reading APIs for various file formats and databases.

- Integrate with an LLM so that the AI can read files or database records and automatically fill in the fields of the forms we define. At this stage, we will probably need an API key for some AI service.

## Final objective

The final goal is to have an application that allows us to create forms at runtime and, through an LLM, extract data to fill out these forms, with the ability to persist the information in various file formats or in a database prepared to receive the data.
