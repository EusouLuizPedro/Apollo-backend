import base64
import io
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Configura a sua chave da API do Gemini diretamente aqui para testar no computador
GEMINI_API_KEY = "AQ.Ab8RN6L5YXde3dqyspXl7JV7ukAl5fINPBdA5OIzRzjFzwKcwg"
genai.configure(api_key=GEMINI_API_KEY)

class AudioRequest(BaseModel):
    audio_base64: str

@app.post("/processar-audio")
async def processar_audio(request: AudioRequest):
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        wav_buffer = io.BytesIO()
        
        num_channels = 1
        sample_rate = 16000
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
