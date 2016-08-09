function scan_barcode(onDetected,except_min_length,width,onFailed)
{
  except_min_length = except_min_length || 5;
  Quagga.init({
      inputStream: {
          type : "LiveStream",
          constraints: {
              width: 640,
              height: 640,
              facingMode: "environment"
          }
      },
      frequency: 2,
      decoder: {
          readers : [ "code_128_reader", "ean_reader" ]
      },
      locate: true,
      patchSize: "medium",
      numOfWorkers: 1
  },
  function(err) {
      if (err)
      {
        console.log(err);
        if (onFailed) onFailed(err);
      }
      Quagga.start();
  });
  Quagga.onProcessed(function(result) {
      var drawingCtx = Quagga.canvas.ctx.overlay,
          drawingCanvas = Quagga.canvas.dom.overlay;

      if (result) {
          if (result.boxes) {
              drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
              result.boxes.filter(function (box) {
                  return box !== result.box;
              }).forEach(function (box) {
                  Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "green", lineWidth: 2});
              });
          }
          if (result.box) {
              Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
          }
          if (result.codeResult && result.codeResult.code) {
              Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
          }
      }
  });
  Quagga.onDetected(function(result) {
      var code = result.codeResult.code;
      console.log(code);
      if (code.length >= except_min_length)
      {
        Quagga.stop();
        if (onDetected)
          onDetected(code);
      }
  });
  return Quagga;
}

function take_snap()
{
  var video = $('video');
  var canvas = document.createElement('canvas');
  canvas.width = video.width();
  canvas.height = video.height();
  var ctx = canvas.getContext('2d');
  ctx.drawImage(video[0], 0, 0, canvas.width, canvas.height);

  //convert to desired file format
  return canvas.toDataURL('image/jpeg'); // can also use 'image/png'
}

function get_code_from_image(url,onDetected,offDetected)
{
  Quagga.decodeSingle({
    src: url,
    decoder: {
        readers: ["code_128_reader","ean_reader"] // List of active readers
    },
    }, function(result) {
        if(result && result.codeResult) {
            console.log("Detected", result.codeResult.code);
        } else {
            console.log("NOT Detected");
        }
    });
}
