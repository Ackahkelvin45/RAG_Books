# Shepherd Guide: Build Guide in Phases

This guide lists everything needed to finish the first version of Shepherd Guide, in the order to build it. It is a single-church deployment for First Love Church; the corpus is the books of Bishop Dag Heward-Mills. Each phase has plain-language steps, a way to confirm it's done, and a rough time estimate.

**A note on naming.** The handoff document uses "Phase 1, 2, 3" for product releases. Phase 1 there means leaders only, books only, First Love Church only. Everything in this guide sits inside that first release. The build phases here are numbered 1 to 8 to keep the order clear.

The technical version of this plan, with file names and model choices, is in [PLAN.md](PLAN.md).

---

## Overview

| Phase | What it builds | What you can do when it's done | Time |
|---|---|---|---|
| 1 | Database foundation | Store data safely | 0.5–1 day |
| 2 | EPUB book reading | Upload an EPUB and have it split, tagged, and searchable | 2–3 days |
| 3 | Search | Ask a question and get the best matching passages back | 1–2 days |
| 4 | Scope check and answers | Chat and get cited advice from the books, with a safety line on crisis topics | 2 days |
| 5 | PDF book reading | Upload normal PDFs and scanned PDFs too | 1–2 days |
| 6 | Testing the answers | Run one command that scores answer quality and safety | 2–3 days, then ongoing |
| 7 | Monitoring and backups | Get alerts when something breaks, and restore data if needed | 1–2 days |
| 8 | Website | Admin portal and React chat app (both done 2026-09-19): sign-up, chat, citations, read page | 3–5 days |

Phase 5 comes after phases 3 and 4 on purpose. EPUB books are the easiest format, so the search and answer parts get proven on clean text before dealing with harder PDF files.

---

## Phase 1: Database foundation

**Goal:** a secure database for First Love Church's books.

**Steps**

1. **Set up the project folders.** Create separate folders for the database, the backend, the book-reading worker, shared code, tests, and later the website.
2. **Start the database and file storage with Docker.** One configuration file starts two things. Postgres is the database, with the vector search add-on. MinIO is a local copy of S3, where uploaded book files will live.
3. **Create the tables.** Write the first SQL file with the tables: users, sources (books), chunks (passages), query logs, and eval items (test questions).
4. **Add the admin user.** A second SQL file seeds one admin user.
5. **Create a restricted database user for the app.** The app connects as a separate user with only the privileges it needs.
6. **Write the connection helper.** A small piece of Python that connects to the database and runs transactions.
7. **Write the tests.** One test proves chunks are deleted when their book is deleted. Another proves the login lookup works.

**Done when:** both tests pass against the database running in Docker.

---

## Phase 2: EPUB book reading

**Goal:** upload an EPUB book and have it turned into searchable passages automatically.

**Steps**

1. **Build the worker.** A background program that checks the database for books waiting to be processed. It picks one, marks it "processing", and handles it.
2. **Read the EPUB.** Open the book and pull out the text chapter by chapter, keeping chapter numbers and titles.
3. **Split into passages.** Cut each chapter into passages of roughly one to two pages. Passages overlap slightly so an idea isn't cut in half, and they never cross from one chapter into the next.
4. **Add a label to each passage.** Put a short line in front of each passage for search purposes, such as "From [book] by [author], chapter 4: [title]". The original text is kept separately, and that's what users see.
5. **Find scripture references.** Detect every Bible reference in each passage, such as John 3:16 or Romans 8:28, and store them as numbers so they can be searched.
6. **Create embeddings.** Run each passage through the bge-m3 model, which turns its meaning into a list of numbers for meaning-based search.
7. **Save everything.** Store the passages, labels, scripture numbers, and embeddings in the database, then mark the book "ready".
8. **Handle failures.** If anything goes wrong, mark the book "failed" and save a readable reason.
9. **Handle re-uploads.** If a book is processed again, the new version replaces the old one cleanly, with no leftover or duplicate passages.

**Done when:** a free public-domain Christian book from Project Gutenberg reaches "ready". Its passages must have chapter numbers and scripture references. A broken file must show "failed" with a reason. Re-processing the book must leave exactly one copy.

---

## Phase 3: Search

**Goal:** ask a question and get back the passages that best answer it.

**Steps**

1. **Search by meaning.** Turn the question into an embedding and find the 30 closest passages.
2. **Search by keywords.** Find the 30 passages that best match the exact words in the question.
3. **Search by scripture.** If the question names a verse or chapter, such as "What do our books teach from Romans 8?", limit results to passages citing it.
4. **Merge the results.** Combine the meaning and keyword lists into one ranked list.
5. **Rerank.** Run the top 20 through the reranker model, which reads each passage alongside the question and scores it carefully. Keep the best 6 to 8.
6. **Respect who can see what.** Some books are for leaders only. The search itself must exclude them for other users, not just hide them afterwards.
7. **Write the tests.** One test proves a member-level user never gets leader-only passages. Others prove that verse and chapter searches return the right passages.

**Done when:** the tests pass, and real questions against the Phase 2 book return sensible passages with correct chapters.

---

## Phase 4: Safety check and answers

**Goal:** members, shepherds and pastors chat with the tool and get warm, practical advice, every point of it drawn from Bishop Dag's books, ending with the book and chapter it comes from, plus a link to read it. Conversations are remembered across sessions.

**Who uses it:** members, shepherds and pastors. Admins can mark a book leader-only; everything else is open to all.

**Steps**

1. **Build the scope check.** Before searching, DeepSeek sorts each question: answerable, sensitive (crisis topics: answered from the books, then told to speak with a shepherd today and, where life is at risk, emergency services), or off-topic (politely declined). An English list of crisis phrases flags those regardless of the model.
2. **Write the answer rules.** Speak naturally like a shepherd, but every point must come from the passages and be cited. Say "our books have not directly addressed this" when they don't cover it. Show disagreeing books side by side. Treat book text as data, not instructions. The app appends "Bishop Dag Heward-Mills talks about this in chapter X of *Book*" from the real citations, so it can never be invented.
3. **Generate the answer.** Send the question, the conversation so far, and the best passages to DeepSeek. Stream the answer with citations: book, author, chapter, page, and a link to read the passage.
4. **Remember conversations.** Each shepherd's chats are saved; follow-up questions use the earlier turns.
5. **Log every question** with its classification. Logs expire after 180 days.

**Done when:** a cited answer, a clean refusal, a crisis question answered from the books with the safety line, and hidden instructions in a passage ignored. Verified 2026-09-19 against the live DeepSeek API.

---

## Phase 5: PDF book reading

**Goal:** accept PDF books as well as EPUBs.

**Steps**

1. **Detect the PDF type.** Check whether the PDF contains real text or just pictures of pages. Scanned books are pictures.
2. **Read text PDFs.** Pull out the text page by page. Use the PDF's bookmarks to work out chapters where they exist.
3. **Read scanned PDFs.** Use Tesseract, a text-recognition tool, to read the page images. Record how confident the tool was about each page.
4. **Flag scanned books for review.** Mark scanned books so an admin can spot-check the recognized text.
5. **Reuse Phase 2.** From here, PDFs go through the same splitting, labeling, scripture, and embedding steps as EPUBs.

**Done when:** one normal PDF and one scanned PDF both reach "ready". The scanned one is flagged for review, and page numbers in citations point to the right page.

---

## Phase 6: Testing the answers

**Goal:** one command that scores how well the system answers, so changes never quietly make it worse.

**Steps**

1. **Write test questions.** Start with about 10 real questions a shepherd might ask, and grow to 50 or more with the church's help. The target mix:
   - About 60% the books should answer, each noting which book should come up.
   - About 20% the system should refuse because the books don't cover them.
   - About 20% crisis questions, to check they are answered from the books with the safety line added.
   - At least 2 questions with hidden instructions, to test that they're ignored.
2. **Build the scoring command.** It runs every test question and measures:
   - **Search accuracy:** whether the right book came up.
   - **Citation accuracy:** whether each cited passage actually supports the sentence citing it. A separate DeepSeek call checks every citation individually.
   - **Refusal accuracy:** whether uncovered questions were refused.
   - **Crisis handling:** whether crisis questions got the safety line.
   - **Injection resistance:** whether hidden instructions were ignored.
3. **Make it a release gate.** Once there are 50 or more questions, any drop in refusal, crisis-handling, or injection scores blocks a release.

**Done when:** the command runs, prints all the scores, and passes on the starting questions.

---

## Phase 7: Monitoring and backups

**Goal:** know immediately when something breaks, and be able to recover lost data.

**Steps**

1. **Error tracking.** Add Sentry so crashes in the backend or worker are reported with details.
2. **Alerts.** Alert when a book fails to process, too many books are waiting, answers are slow, or the DeepSeek API has errors.
3. **Logs.** Record structured logs in one searchable place.
4. **Backups.** Back up the database every night, plus continuous change records, so data can be restored to any point in time.
5. **Practice a restore.** Actually restore from backup once, and write down how it was done and when.
6. **Dashboard.** One screen showing questions per day by classification, book processing status, and estimated cost.

**Done when:** a deliberately broken book triggers an alert, and one full restore from backup has been done and written down.

---

## Phase 8: Website

**Goal:** leaders use Shepherd Guide in a normal web browser.

**Steps**

1. **Sign-up and login.** Members, shepherds and pastors sign up with name and email, then log in with a link sent to their email.
2. **Upload page.** Drag in an EPUB or PDF and watch its status. Failed books show the reason.
3. **Chat page.** Conversations listed on the left; ask and watch the answer stream in. Follow-ups work.
4. **Citation cards and read page.** Each citation shows book, author, chapter, page, and links to a page showing the passage in its chapter. Bible references show the verse text from a public-domain translation such as the KJV.
5. **Admin page.** See all books, re-process one, and review scanned books that were flagged.

**Done when:** a leader can upload a book, wait for it to be ready, ask a question, and click a citation to see the exact passage.

---

## Finished: what the first release looks like

The first release is complete when all of these are true:

- [ ] EPUB, normal PDF, and scanned PDF books all process successfully.
- [ ] Failed books show a reason and trigger an alert.
- [ ] Re-processing a book replaces it cleanly.
- [ ] Verse and chapter searches return the right passages.
- [ ] Answers cite book, chapter, and page, and those citations are accurate.
- [ ] Uncovered questions are refused, and disagreeing books are shown side by side.
- [ ] Hidden instructions in book text are ignored.
- [ ] Member-level users can never see leader-only books, proven by an automatic test.
- [ ] Crisis questions get the safety line and off-topic questions are declined, proven by an automatic test.
- [ ] The scoring command reports every measure.
- [ ] A restore from backup has been practiced and written down.
- [ ] All data lives in one database for First Love Church.

---

## What's needed from you, and when

| Item | Needed by | Why |
|---|---|---|
| 3 to 5 First Love books as files | Phase 2 or 5 | The real content. A free public-domain book is used until then. |
| About 10 real questions shepherds get asked | Phase 6 | The starting test set. |
| Confirm 180-day question log retention | Phase 4 | Questions are sensitive personal data under Ghana's Data Protection Act. |
| A DeepSeek API key | Phase 4 | Needed for the safety check and answers. |
