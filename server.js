require('dotenv').config();
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const pdfParse = require('pdf-parse');
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');

const app = express();
const prisma = new PrismaClient();
const upload = multer({ dest: 'uploads/' });

app.use(cors());
app.use(express.json());

app.get('/health', (_, res) => res.json({ ok: true, time: new Date().toISOString() }));

app.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
    const title = req.body?.title || req.file.originalname;
    const lecture = await prisma.lecture.create({
      data: { title, filePath: req.file.path, status: 'UPLOADED' }
    });
    res.status(201).json(lecture);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'Upload failed' });
  }
});

app.post('/analyze/:id', async (req, res) => {
  try {
    const lecture = await prisma.lecture.findUnique({ where: { id: req.params.id } });
    if (!lecture) return res.status(404).json({ error: 'Lecture not found' });

    const dataBuffer = fs.readFileSync(lecture.filePath);
    const pdfData = await pdfParse(dataBuffer);
    const text = (pdfData.text || '').replace(/\s+/g, ' ').trim();

    const words = [...new Set(text.split(/\W+/).filter(w => w.length > 5))];
    const base = words.slice(0, 25);
    const questions = [];
    for (let i = 0; i < Math.min(5, base.length - 3); i++) {
      const correct = base[i];
      const distractors = base.filter(w => w !== correct).slice(i + 1, i + 4);
      const options = [correct, ...distractors].sort(() => Math.random() - 0.5);
      questions.push({
        content: `Энэ лекцтэй хамгийн холбоотой түлхүүр үг аль нь вэ?`,
        options: JSON.stringify(options),
        answer: correct,
        difficulty: 1,
        lectureId: lecture.id
      });
    }
    for (const q of questions) await prisma.question.create({ data: q });
    await prisma.lecture.update({ where: { id: lecture.id }, data: { status: 'READY' } });
    res.json({ ok: true, questionsCreated: questions.length });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'Analyze failed' });
  }
});

app.get('/lectures/:id/questions', async (req, res) => {
  const items = await prisma.question.findMany({ where: { lectureId: req.params.id } });
  res.json({ items, total: items.length });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server running at http://localhost:${PORT}`));

app.get('/', (_, res) => res.send(`
    <form method="post" action="/upload" enctype="multipart/form-data">
      <input type="file" name="file" />
      <input type="text" name="title" value="Test Lecture" />
      <button type="submit">Upload</button>
    </form>
  `));
  