const express = require('express');
const { getTranscript } = require('youtube-transcript');

const app = express();
app.use(express.json());

app.post('/transcript', async (req, res) => {
  const { videoId } = req.body;
  try {
    const transcript = await getTranscript(videoId);
    res.json({ transcript });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = 4000;
app.listen(PORT, () => console.log(`Transcript server running on port ${PORT}`)); 