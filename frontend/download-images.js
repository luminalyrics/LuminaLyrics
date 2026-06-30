const fs = require('fs');
const https = require('https');
const path = require('path');

const urls = [
  "https://images.unsplash.com/photo-1516280440502-850f229a1740?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1493225457124-a1a2a5f5646a?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1520690214124-2405c5217036?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1598387181032-a3103a2db5b3?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1470229722913-7c092b322233?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1471478330526-517d965b36e4?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1458560871784-56d23406c091?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1485030056468-3820ff9e6e90?q=80&w=600&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1522863602463-afebb88d5942?q=80&w=600&auto=format&fit=crop"
];

const targetDir = path.join(__dirname, 'src', 'assets', 'images', 'home');

if (!fs.existsSync(targetDir)){
    fs.mkdirSync(targetDir, { recursive: true });
}

urls.forEach((url, index) => {
  const file = fs.createWriteStream(path.join(targetDir, `img-${index + 1}.jpg`));
  https.get(url, function(response) {
    response.pipe(file);
    file.on('finish', function() {
      file.close();  
      console.log(`Downloaded img-${index + 1}.jpg`);
    });
  }).on('error', function(err) {
    fs.unlink(path.join(targetDir, `img-${index + 1}.jpg`), () => {});
    console.error(`Error downloading img-${index + 1}.jpg: ${err.message}`);
  });
});
