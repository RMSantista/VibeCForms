# Learning Notes

## Initial Experience

In my first prompt, I made some mistakes:

1. I asked for the code to be generated, unit tests to be executed, and the browser to open automatically to see the program running. I naively thought it would be that magical. In reality, it generated the main program file, the tests, and gave me a series of commands to run in the terminal to get the program working. It was a bit frustrating because I expected a result similar to what I had seen done with Cline, for example (which requires an AI license key). I still don't know if an equivalent result is possible with just GitHub Copilot, since apparently it can't interact with the VSCode terminal. But I took a deep breath, ran the necessary commands in the terminal, and moved forward. I ran the unit tests, which passed, and then ran the program.

2. Another point where I was naive was believing that by asking for a CRUD, it would already create an application that could create, read, update, and delete records. Since I only mentioned that I wanted it to register clients and persist them in a text file, without mentioning update and delete, the first program it generated contained the specified fields (name, phone, WhatsApp) and allowed registration, but only registration.

3. This one I don't even consider a mistake. I didn't provide any information about the application's appearance. So, when it generated the first program, it had no layout, just a set of three fields one below the other and a register button, which, when clicked, saved the data to a txt file as requested and displayed the registered data below on the screen.

## Completing the CRUD

I needed to make the rest of the CRUD work, which led to the second prompt, asking to complete the CRUD by implementing the update and delete functions and their respective unit tests. At this point, the AI was already aligned with what we were doing, and even though the prompt was simple, it followed the instructions correctly. I ran the unit tests, which again passed, and restarted the application. It was indeed allowing me to update and delete records as it should. However, the layout was still "raw"; it used hyperlinks for these new functionalities. I was happy because it was working, but bothered by the program's appearance.

## Improving the Layout

This led to the third prompt. This was also a simple prompt. I said the layout was "raw" and asked for some CSS to be applied to the system, giving some generic specifications of what I wanted. The AI really aligned the fields, put everything in a panel, started displaying the data in a table, and replaced the hyperlinks with buttons and icons. This made me happier because the application not only worked but was also more presentable.

## Addressing Details

However, some details still bothered me:

- The alignment of the Register button.
- The fact that pressing Enter would reload the form and register immediately.
- The records occupying two lines in the table where they are displayed.

This led to prompts 4 and 5, where I simply asked to fix these details, and GitHub Copilot adjusted them beautifully.

## Validation

The visual was now nice. However, my last few years of work were as a QA, so being able to create registrations without information seemed unacceptable to me. Of course, many other validations could be done, but I wanted at least the minimum. This led to the last prompt, where I requested that registration without name or phone not be allowed. In this prompt, I was more specific, as I didn't want empty fields to be registered, but also didn't want the messages to remain on the screen after the fields were filled.

