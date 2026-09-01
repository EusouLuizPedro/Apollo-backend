import base64
import io
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Configura a sua chave da API do Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDO6xLqc9xbQP7rNd2CFb7lEqOPr5CZojU")
genai.configure(api_key=GEMINI_API_KEY)

# Variável global temporária para armazenar os bytes do último áudio gravado
ultimo_audio_wav = None

class AudioRequest(BaseModel):
    audio_base64: str

@app.post("/processar-audio")
async def processar_audio(request: AudioRequest):
    global ultimo_audio_wav
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        wav_buffer = io.BytesIO()
        
        num_channels = 1
        sample_rate = 11025  # Taxa combinada com seu ESP32
        bits_per_sample = 16
        data_size = len(audio_bytes)
        
        wav_buffer.write(b'RIFF')
        wav_buffer.write((data_size + 36).to_bytes(4, 'little'))
        wav_buffer.write(b'WAVEfmt ')
        wav_buffer.write((16).to_bytes(4, 'little'))
        wav_buffer.write((1).to_bytes(2, 'little'))
        wav_buffer.write((num_channels).to_bytes(2, 'little'))
        wav_buffer.write((sample_rate).to_bytes(4, 'little'))
        wav_buffer.write((sample_rate * num_channels * bits_per_sample // 8).to_bytes(4, 'little'))
        wav_buffer.write((num_channels * bits_per_sample // 8).to_bytes(2, 'little'))
        wav_buffer.write((bits_per_sample).to_bytes(2, 'little'))
        wav_buffer.write(b'data')
        wav_buffer.write((data_size).to_bytes(4, 'little'))
        
        wav_buffer.write(audio_bytes)
        wav_data = wav_buffer.getvalue()

        # Salva uma cópia na memória do servidor para você conseguir ouvir
        ultimo_audio_wav = wav_data

        model = genai.GenerativeModel("gemini-3.5-flash")
        
        prompt_apollo = (
            "Você é o Apollo, uma inteligência artificial criada por Luiz Pedro, uma criança de 12 anos "
            "hobbista em robótica e mecatrônica. Sempre responda em Português Brasil de forma curta, "
            "educada e gentil. Responda diretamente ao áudio enviado."
        )

        response = model.generate_content([
            {
                "mime_type": "audio/wav",
                "data": wav_data
            },
            prompt_apollo
        ])

        return {"resposta": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ROTA NOVA: Serve apenas para você baixar e escutar o som no seu navegador
@app.get("/baixar-audio")
async def baixar_audio():
    global ultimo_audio_wav
    if ultimo_audio_wav is None:
        return {"erro": "Nenhum áudio foi gravado ainda. Ligue o ESP32 e fale no microfone primeiro!"}
    
    # Retorna o arquivo de som bruto formatado como um download de áudio/wav
    return Response(content=ultimo_audio_wav, media_type="audio/wav", headers={"Content-Disposition": "attachment; filename=gravação_apollo.wav"})


