const video = document.getElementById('camera'), canvas = document.getElementById('canvas');
const start = document.getElementById('start'), capture = document.getElementById('capture'), statusText = document.getElementById('camera-status');
start?.addEventListener('click', async () => {
  try { video.srcObject = await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false}); await video.play(); capture.disabled=false; start.disabled=true; statusText.textContent='Camera ready. Capture clear samples.'; }
  catch(e) { statusText.textContent='Camera permission was denied or no camera was found.'; }
});
capture?.addEventListener('click', async () => {
  if (!video.videoWidth) return;
  canvas.width=video.videoWidth; canvas.height=video.videoHeight; canvas.getContext('2d').drawImage(video,0,0);
  const data=new FormData(); data.append('student_id',document.getElementById('student').value); data.append('image',canvas.toDataURL('image/jpeg',.9));
  capture.disabled=true; statusText.textContent='Detecting face…';
  try { const response=await fetch('/api/enrol',{method:'POST',body:data}); const result=await response.json(); statusText.textContent=result.ok ? `${result.message}. Total samples: ${result.count}` : result.message; }
  catch(e) { statusText.textContent='Could not save sample. Please try again.'; } finally { capture.disabled=false; }
});
