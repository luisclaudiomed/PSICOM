#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PSICOM: Sistema Avançado de Análise de Comunicação Interpessoal
Versão: 3.0
Framework de análise comportamental e psicológica para otimização de comunicação profissional
"""

import os
import re
import json
import sys
import datetime
import subprocess
import statistics
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import pickle
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
import csv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("psicom.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PSICOM")

class PsychologicalAnalysisSystem:
    """Sistema principal de análise psicológica e comportamental"""
    
    def __init__(self):
        """Inicializa o sistema de análise com configurações padrão"""
        # Definir caminhos e configurações
        self.config = self.load_configuration()
        
        # Inicializar diretórios necessários
        self.initialize_directories()
        
        # Carregar modelos de análise
        self.models = self.load_analysis_models()
        
        # Carregar perfis existentes
        self.profiles = self.load_profiles()
        
        # Estado atual do sistema
        self.current_profile = None
        self.current_analysis = None
        self.conversation_data = None
        self.current_workspace = None
        
        # Thread pool para processamento paralelo
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Inicializar interface gráfica
        self.initialize_gui()
    
    def load_configuration(self):
        """Carrega configurações do sistema ou cria configurações padrão"""
        default_config = {
            "APP_NAME": "PSICOM",
            "VERSION": "3.0",
            "BASE_DIR": os.path.expanduser("~/PSICOM"),
            "PROFILES_DIR": os.path.expanduser("~/PSICOM/profiles"),
            "DATA_DIR": os.path.expanduser("~/PSICOM/data"),
            "MODELS_DIR": os.path.expanduser("~/PSICOM/models"),
            "WORKSPACE_DIR": os.path.expanduser("~/PSICOM/workspaces"),
            "EXPORT_DIR": os.path.expanduser("~/PSICOM/exports"),
            "TEMP_DIR": os.path.expanduser("~/PSICOM/temp"),
            "LOG_DIR": os.path.expanduser("~/PSICOM/logs"),
            
            # Configurações de ferramentas externas
            "OPENSMILE_PATH": "",
            "OPENSMILE_CONFIG": "",
            "FFMPEG_PATH": "ffmpeg",
            
            # Configurações de análise
            "WHISPER_MODEL": "medium",  # tiny, base, small, medium, large
            "DEFAULT_LANGUAGE": "pt",
            "EMOTION_SENSITIVITY": 0.5,  # 0.0 a 1.0
            "CONTEXT_WINDOW_SIZE": 5,    # Número de mensagens a considerar para contexto
            
            # Preferências de interface
            "UI_THEME": "default",
            "COLOR_SCHEME": "light",
            "CHART_STYLE": "seaborn",
            "FONT_SIZE": 10,
            
            # Configurações avançadas
            "AUTO_BACKUP": True,
            "BACKUP_INTERVAL": 30,  # minutos
            "ANONYMIZE_DATA": False,
            "ENABLE_ADVANCED_ANALYSIS": True
        }
        
        config_path = os.path.expanduser("~/PSICOM/config.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Atualizar configuração padrão com valores carregados
                for key, value in loaded_config.items():
                    default_config[key] = value
                
                logger.info("Configurações carregadas com sucesso")
            else:
                logger.info("Arquivo de configuração não encontrado. Usando configurações padrão")
                
                # Criar diretório base
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Salvar configurações padrão
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Configurações padrão salvas em {config_path}")
        
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            logger.info("Usando configurações padrão")
        
        return default_config
    
    def save_configuration(self):
        """Salva as configurações atuais do sistema"""
        config_path = os.path.expanduser("~/PSICOM/config.json")
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Configurações salvas em {config_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def initialize_directories(self):
        """Cria os diretórios necessários para o sistema"""
        directories = [
            self.config["BASE_DIR"],
            self.config["PROFILES_DIR"],
            self.config["DATA_DIR"],
            self.config["MODELS_DIR"],
            self.config["WORKSPACE_DIR"],
            self.config["EXPORT_DIR"],
            self.config["TEMP_DIR"],
            self.config["LOG_DIR"]
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"Diretório criado/verificado: {directory}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório {directory}: {e}")
    
    def load_analysis_models(self):
        """Carrega modelos de análise ou cria novos se não existirem"""
        models = {
            "personality_classifier": None,
            "emotion_analyzer": None,
            "behavioral_patterns": None,
            "response_predictor": None,
            "topic_classifier": None,
            "persuasion_predictor": None
        }
        
        # Verificar e carregar modelos existentes
        for model_name in models.keys():
            model_path = os.path.join(self.config["MODELS_DIR"], f"{model_name}.pkl")
            
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'rb') as f:
                        models[model_name] = pickle.load(f)
                    logger.info(f"Modelo {model_name} carregado com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao carregar modelo {model_name}: {e}")
            else:
                logger.info(f"Modelo {model_name} não encontrado")
                # Os modelos ausentes serão criados sob demanda durante a análise
        
        return models
    
    def load_profiles(self):
        """Carrega perfis existentes do diretório de perfis"""
        profiles = {}
        
        try:
            profile_files = [f for f in os.listdir(self.config["PROFILES_DIR"]) 
                           if f.endswith('.json')]
            
            for profile_file in profile_files:
                profile_path = os.path.join(self.config["PROFILES_DIR"], profile_file)
                
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        profile_id = os.path.splitext(profile_file)[0]
                        profiles[profile_id] = profile_data
                        logger.debug(f"Perfil carregado: {profile_id}")
                except Exception as e:
                    logger.error(f"Erro ao carregar perfil {profile_file}: {e}")
            
            logger.info(f"{len(profiles)} perfis carregados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao acessar diretório de perfis: {e}")
        
        return profiles
    
    def create_new_profile(self, name, description="", additional_data=None):
        """Cria um novo perfil de pessoa para análise"""
        # Gerar ID único baseado no nome
        profile_id = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        
        # Verificar se já existe perfil com esse ID
        if profile_id in self.profiles:
            # Gerar ID único adicionando um número
            base_id = profile_id
            counter = 1
            while profile_id in self.profiles:
                profile_id = f"{base_id}_{counter}"
                counter += 1
        
        # Estrutura base do perfil
        profile_data = {
            "profile_id": profile_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "analyses": [],
            "behavioral_patterns": {
                "communication_style": {},
                "emotional_patterns": {},
                "response_patterns": {},
                "linguistic_patterns": {},
                "topic_preferences": {},
                "persuasion_indicators": {}
            },
            "communication_stats": {},
            "psychological_profile": {
                "personality_traits": {},
                "cognitive_patterns": {},
                "emotional_tendencies": {},
                "motivation_factors": {},
                "communication_preferences": {}
            },
            "recommendations": {
                "general": [],
                "by_topic": {},
                "by_context": {}
            }
        }
        
        # Adicionar dados adicionais se fornecidos
        if additional_data and isinstance(additional_data, dict):
            for key, value in additional_data.items():
                if key not in profile_data:
                    profile_data[key] = value
        
        # Salvar perfil
        profile_path = os.path.join(self.config["PROFILES_DIR"], f"{profile_id}.json")
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            
            # Adicionar à coleção de perfis
            self.profiles[profile_id] = profile_data
            
            logger.info(f"Novo perfil criado: {profile_id} ({name})")
            return profile_id
        except Exception as e:
            logger.error(f"Erro ao criar perfil {name}: {e}")
            return None
    
    def update_profile(self, profile_id, updated_data):
        """Atualiza um perfil existente"""
        if profile_id not in self.profiles:
            logger.error(f"Perfil não encontrado: {profile_id}")
            return False
        
        # Fazer backup do perfil atual
        backup_dir = os.path.join(self.config["PROFILES_DIR"], "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = f"{profile_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_file)
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles[profile_id], f, ensure_ascii=False, indent=2)
            
            # Atualizar perfil com novos dados
            for key, value in updated_data.items():
                # Não substituir campos estruturais
                if key not in ["profile_id", "created_at", "analyses"]:
                    self.profiles[profile_id][key] = value
            
            # Atualizar timestamp
            self.profiles[profile_id]["last_updated"] = datetime.now().isoformat()
            
            # Salvar perfil atualizado
            profile_path = os.path.join(self.config["PROFILES_DIR"], f"{profile_id}.json")
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles[profile_id], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Perfil atualizado: {profile_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil {profile_id}: {e}")
            return False
    
    def delete_profile(self, profile_id):
        """Exclui um perfil existente"""
        if profile_id not in self.profiles:
            logger.error(f"Perfil não encontrado: {profile_id}")
            return False
        
        # Fazer backup do perfil
        backup_dir = os.path.join(self.config["PROFILES_DIR"], "deleted")
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = f"{profile_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_file)
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles[profile_id], f, ensure_ascii=False, indent=2)
            
            # Remover arquivo do perfil
            profile_path = os.path.join(self.config["PROFILES_DIR"], f"{profile_id}.json")
            
            if os.path.exists(profile_path):
                os.remove(profile_path)
            
            # Remover da coleção de perfis
            del self.profiles[profile_id]
            
            logger.info(f"Perfil excluído: {profile_id}")
            
            # Se for o perfil atual, limpar referência
            if self.current_profile == profile_id:
                self.current_profile = None
            
            return True
        
        except Exception as e:
            logger.error(f"Erro ao excluir perfil {profile_id}: {e}")
            return False
    
    # =========================================================================
    # Processamento de conversas e análise de dados
    # =========================================================================
    
    def load_whatsapp_chat(self, file_path):
        """Carrega e processa o arquivo de chat do WhatsApp exportado"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                chat_text = file.read()
            
            # Padrão para mensagens do WhatsApp
            message_pattern = re.compile(r'\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] ([^:]+): (.*)', re.DOTALL)
            
            messages = []
            
            # Iterar pelos matches encontrados
            for match in message_pattern.finditer(chat_text):
                date_str, time_str, author, content = match.groups()
                
                # Converter strings de data e hora para objeto datetime
                date_time_str = f"{date_str} {time_str}"
                dt = datetime.strptime(date_time_str, '%d/%m/%Y %H:%M:%S')
                
                # Detectar tipo de conteúdo (texto, áudio, imagem, etc.)
                content_type, media_file = self.detect_content_type(content)
                
                # Preparar estrutura de dados para a mensagem
                message = {
                    'id': f"msg_{len(messages)}_{dt.strftime('%Y%m%d%H%M%S')}",
                    'datetime': dt.isoformat(),
                    'date': dt.date().isoformat(),
                    'time': dt.time().isoformat(),
                    'timestamp': dt.timestamp(),
                    'author': author.strip(),
                    'content': content.strip(),
                    'content_type': content_type,
                    'media_file': media_file,
                    'is_target': self.is_target_person(author.strip()),
                    'media_processed': False,
                    'transcription': None,
                    'analysis': {
                        'emotion': None,
                        'attitude': None,
                        'themes': [],
                        'behavioral_indicators': {},
                        'psychological_indicators': {},
                        'linguistic_analysis': {}
                    },
                    'context': {
                        'previous_messages': [],
                        'conversation_state': None,
                        'user_observations': None
                    }
                }
                
                messages.append(message)
            
            logger.info(f"Conversa carregada: {len(messages)} mensagens")
            return messages
        
        except Exception as e:
            logger.error(f"Erro ao carregar conversa: {e}")
            return []
    
    def detect_content_type(self, content):
        """Detecta o tipo de conteúdo e arquivo de mídia associado"""
        content = content.strip()
        
        # Padrões para diferentes tipos de mídia
        audio_pattern = re.compile(r'(PTT-\d{8}-WA\d{4}\.opus)')
        image_pattern = re.compile(r'(IMG-\d{8}-WA\d{4}\.(jpg|jpeg|png))')
        video_pattern = re.compile(r'(VID-\d{8}-WA\d{4}\.(mp4|3gp))')
        document_pattern = re.compile(r'([^<>:"/\\|?*]+\.(pdf|doc|docx|xls|xlsx|txt))')
        
        # Verificar áudio
        audio_match = audio_pattern.search(content)
        if audio_match:
            return 'audio', audio_match.group(1)
        
        # Verificar imagem
        image_match = image_pattern.search(content)
        if image_match:
            return 'image', image_match.group(1)
        
        # Verificar vídeo
        video_match = video_pattern.search(content)
        if video_match:
            return 'video', video_match.group(1)
        
        # Verificar documento
        document_match = document_pattern.search(content)
        if document_match:
            return 'document', document_match.group(1)
        
        # Texto comum
        return 'text', None
    
    def is_target_person(self, author):
        """Verifica se o autor da mensagem é a pessoa-alvo"""
        if not self.current_profile or not self.profiles.get(self.current_profile):
            return False
        
        target_name = self.profiles[self.current_profile]["name"]
        return target_name.lower() in author.lower()
    
    def process_media_files(self, conversation, source_dir, progress_callback=None):
        """Processa todos os arquivos de mídia na conversa"""
        # Contar total de arquivos de mídia
        media_files = [msg for msg in conversation if msg['content_type'] != 'text' and msg['media_file']]
        total_media = len(media_files)
        processed = 0
        
        if total_media == 0:
            logger.info("Nenhum arquivo de mídia para processar")
            return conversation
        
        logger.info(f"Processando {total_media} arquivos de mídia")
        
        # Criar diretório para mídia do perfil atual
        profile_media_dir = os.path.join(self.config["DATA_DIR"], self.current_profile, "media")
        os.makedirs(profile_media_dir, exist_ok=True)
        
        # Processar cada arquivo de mídia
        for msg in media_files:
            try:
                media_file = msg['media_file']
                source_path = os.path.join(source_dir, media_file)
                
                # Verificar se o arquivo existe
                if not os.path.exists(source_path):
                    logger.warning(f"Arquivo não encontrado: {source_path}")
                    continue
                
                # Definir caminho de destino
                dest_path = os.path.join(profile_media_dir, media_file)
                
                # Copiar arquivo se não existir
                if not os.path.exists(dest_path):
                    shutil.copy2(source_path, dest_path)
                    logger.debug(f"Arquivo copiado: {media_file}")
                
                # Processar conforme o tipo de mídia
                if msg['content_type'] == 'audio':
                    self.process_audio_file(msg, dest_path)
                elif msg['content_type'] == 'image':
                    self.process_image_file(msg, dest_path)
                elif msg['content_type'] == 'video':
                    self.process_video_file(msg, dest_path)
                
                # Marcar como processado
                msg['media_processed'] = True
                
                # Atualizar progresso
                processed += 1
                if progress_callback:
                    progress_callback(processed / total_media)
                    
            except Exception as e:
                logger.error(f"Erro ao processar mídia {msg.get('media_file', 'desconhecida')}: {e}")
        
        logger.info(f"Processamento de mídia concluído: {processed}/{total_media} arquivos")
        return conversation
    
    def process_audio_file(self, message, audio_path):
        """Processa um arquivo de áudio: converte, transcreve e analisa"""
        try:
            # Converter de .opus para .wav
            wav_path = audio_path.replace('.opus', '.wav')
            
            if not os.path.exists(wav_path):
                self.convert_audio_to_wav(audio_path, wav_path)
            
            # Transcrever o áudio
            transcription = self.transcribe_audio(wav_path)
            message['transcription'] = transcription
            
            # Analisar emoções no áudio
            emotion_analysis = self.analyze_audio_emotion(wav_path)
            message['analysis']['emotion'] = emotion_analysis
            
            logger.debug(f"Áudio processado: {os.path.basename(audio_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar áudio {os.path.basename(audio_path)}: {e}")
            return False
    
    def convert_audio_to_wav(self, input_path, output_path):
        """Converte um arquivo de áudio para o formato WAV usando FFmpeg"""
        try:
            # Construir comando
            ffmpeg_cmd = [
                self.config["FFMPEG_PATH"],
                "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                "-y",
                output_path
            ]
            
            # Executar comando
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            logger.debug(f"Áudio convertido: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao converter áudio com FFmpeg: {e}")
            logger.debug(f"Saída de erro do FFmpeg: {e.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        except Exception as e:
            logger.error(f"Erro ao converter áudio: {e}")
            return False
    
    def transcribe_audio(self, audio_path):
        """Transcreve o áudio usando Whisper"""
        try:
            # Importação condicional para permitir execução sem whisper instalado
            import whisper
            
            logger.info(f"Transcrevendo áudio: {os.path.basename(audio_path)}")
            
            # Carregar modelo
            model = whisper.load_model(self.config["WHISPER_MODEL"])
            
            # Transcrever
            result = model.transcribe(
                audio_path, 
                language=self.config["DEFAULT_LANGUAGE"],
                fp16=False
            )
            
            logger.debug(f"Transcrição concluída: {os.path.basename(audio_path)}")
            return result["text"]
            
        except ImportError:
            logger.warning("Biblioteca Whisper não encontrada. Usando modo simulado.")
            return f"[Simulação de transcrição para {os.path.basename(audio_path)}]"
            
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio: {e}")
            return f"[Erro na transcrição: {str(e)}]"
    
    def analyze_audio_emotion(self, audio_path):
        """Analisa emoções no áudio usando OpenSMILE ou modelo personalizado"""
        # Verificar se OpenSMILE está configurado
        if self.config["OPENSMILE_PATH"] and os.path.exists(self.config["OPENSMILE_PATH"]):
            return self.analyze_with_opensmile(audio_path)
        else:
            # Usar método alternativo para análise
            return self.analyze_audio_features(audio_path)
    
    def analyze_with_opensmile(self, audio_path):
        """Analisa áudio usando OpenSMILE para extração de características emocionais"""
        try:
            # Arquivo temporário para saída
            output_file = os.path.join(
                self.config["TEMP_DIR"], 
                f"{os.path.basename(audio_path)}_egemaps.csv"
            )
            
            # Construir comando do OpenSMILE
            opensmile_cmd = [
                self.config["OPENSMILE_PATH"],
                "-C", self.config["OPENSMILE_CONFIG"],
                "-I", audio_path,
                "-O", output_file
            ]
            
            # Executar comando
            subprocess.run(
                opensmile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Processar resultados
            emotion_data = self.process_opensmile_output(output_file)
            
            # Limpar arquivo temporário
            if os.path.exists(output_file):
                os.remove(output_file)
            
            return emotion_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar OpenSMILE: {e}")
            return self.simulate_emotion_analysis(audio_path)
            
        except Exception as e:
            logger.error(f"Erro na análise de emoção com OpenSMILE: {e}")
            return self.simulate_emotion_analysis(audio_path)
    
    def process_opensmile_output(self, csv_path):
        """Processa a saída do OpenSMILE para extrair características emocionais"""
        try:
            # Ler CSV
            df = pd.read_csv(csv_path, sep=';')
            
            # Principais características emocionais
            features = {
                # Energia/intensidade
                'intensity': float(df['loudness_sma3_amean'].values[0]),
                
                # Pitch médio e variação (relacionados à tensão e expressividade)
                'pitch_mean': float(df['F0semitoneFrom27.5Hz_sma3nz_amean'].values[0]),
                'pitch_range': float(df['F0semitoneFrom27.5Hz_sma3nz_stddevNorm'].values[0]),
                
                # Qualidade vocal
                'jitter': float(df['jitterLocal_sma3nz_amean'].values[0]),
                'shimmer': float(df['shimmerLocal_sma3nz_amean'].values[0]),
                
                # Taxas e ritmo
                'speech_rate': float(df['loudnessPeaksPerSec'].values[0]),
                
                # Formantes (qualidade de voz)
                'formant1_mean': float(df['F1frequency_sma3nz_amean'].values[0]),
                'formant1_bandwidth': float(df['F1bandwidth_sma3nz_amean'].values[0])
            }
            
            # Interpretar como emoções
            emotion_analysis = self.map_features_to_emotions(features)
            
            # Incluir as características brutas para análises avançadas
            emotion_analysis['raw_features'] = features
            
            return emotion_analysis
            
        except Exception as e:
            logger.error(f"Erro ao processar saída do OpenSMILE: {e}")
            return self.simulate_emotion_analysis(csv_path)
    
    def map_features_to_emotions(self, features):
        """Mapeia características acústicas para estados emocionais"""
        # Calcular intensidade emocional geral (0-10)
        intensity = min(10, max(1, features['intensity'] * 10))
        
        # Calcular eixos emocionais básicos
        # Valência (negativa-positiva)
        if features['pitch_mean'] > 100 and features['jitter'] < 0.01:
            valence = 0.7  # Provavelmente positiva
        elif features['jitter'] > 0.02 and features['intensity'] < 0.5:
            valence = 0.3  # Provavelmente negativa
        else:
            valence = 0.5  # Neutra
        
        # Ativação (calma-excitada)
        if features['intensity'] > 0.7 or features['speech_rate'] > 0.8:
            arousal = 0.8  # Alta ativação
        elif features['intensity'] < 0.4 and features['speech_rate'] < 0.5:
            arousal = 0.3  # Baixa ativação
        else:
            arousal = 0.5  # Média
        
        # Tensão (relaxada-tensa)
        if features['jitter'] > 0.02 or features['pitch_range'] < 0.2:
            tension = 0.7  # Tensa
        else:
            tension = 0.4  # Relaxada
        
        # Identificar emoções primárias e secundárias
        emotions = []
        
        # Alta valência, alta ativação
        if valence > 0.6 and arousal > 0.6:
            emotions.append("entusiasmo")
        # Alta valência, baixa ativação
        elif valence > 0.6 and arousal < 0.4:
            emotions.append("contentamento")
        # Baixa valência, alta ativação
        elif valence < 0.4 and arousal > 0.6:
            emotions.append("irritação" if tension > 0.6 else "ansiedade")
        # Baixa valência, baixa ativação
        elif valence < 0.4 and arousal < 0.4:
            emotions.append("tristeza")
        # Baixa valência, média ativação, alta tensão
        elif valence < 0.45 and arousal > 0.4 and arousal < 0.6 and tension > 0.6:
            emotions.append("frustração")
        # Média valência, alta tensão
        elif valence > 0.4 and valence < 0.6 and tension > 0.6:
            emotions.append("tensão")
        # Média valência, média ativação, baixa tensão
        elif valence > 0.4 and valence < 0.6 and arousal > 0.4 and arousal < 0.6 and tension < 0.5:
            emotions.append("neutro")
        
        # Detectar hesitação
        if features['pitch_range'] > 0.6 and features['speech_rate'] < 0.6:
            emotions.append("hesitação")
        
        # Detectar confiança
        if features['intensity'] > 0.6 and features['jitter'] < 0.01 and tension < 0.5:
            emotions.append("confiança")
        
        # Se nenhuma emoção foi identificada
        if not emotions:
            emotions.append("neutro")
        
        # Calcular nível de autenticidade emocional (0-100)
        authenticity = 85 - (features['jitter'] * 1000) - (abs(0.5 - tension) * 50)
        authenticity = max(0, min(100, authenticity))
        
        # Resultado final
        return {
            'primary_emotion': emotions[0],
            'emotional_blend': " + ".join(emotions),
            'intensity': round(intensity, 1),
            'valence': round(valence * 10, 1),    # Escala 0-10 para facilitar interpretação
            'arousal': round(arousal * 10, 1),    # Escala 0-10
            'tension': round(tension * 10, 1),    # Escala 0-10
            'authenticity': round(authenticity),  # Porcentagem
            'emotions': emotions
        }
    
    def analyze_audio_features(self, audio_path):
        """Analisa características do áudio usando bibliotecas alternativas"""
        try:
            # Importação condicional
            import librosa
            import numpy as np
            
            # Carregar áudio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extrair características
            # Energia/intensidade
            rms = librosa.feature.rms(y=y)[0]
            intensity = np.mean(rms) / 0.1  # Normalizar
            
            # Pitch estimado e variação
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_mean = np.mean(pitches[magnitudes > np.median(magnitudes)])
            pitch_range = np.std(pitches[magnitudes > np.median(magnitudes)])
            
            # Taxa de cruzamento zero (aspereza)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            jitter = np.std(zcr) / np.mean(zcr) if np.mean(zcr) > 0 else 0
            
            # Medidas espectrais
            spectral_contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))
            
            # Convertendo para o mesmo formato usado pelo OpenSMILE
            features = {
                'intensity': min(1.0, max(0.1, intensity)),
                'pitch_mean': pitch_mean if not np.isnan(pitch_mean) else 100,
                'pitch_range': min(1.0, max(0.1, pitch_range / 100)),
                'jitter': min(0.05, max(0.001, jitter)),
                'shimmer': min(0.1, max(0.01, np.std(rms) / (np.mean(rms) + 1e-10))),
                'speech_rate': min(1.0, max(0.1, np.mean(zcr))),
                'formant1_mean': 500,  # Valor aproximado
                'formant1_bandwidth': 100  # Valor aproximado
            }
            
            # Mapear para emoções
            emotion_analysis = self.map_features_to_emotions(features)
            emotion_analysis['raw_features'] = features
            
            return emotion_analysis
            
        except ImportError:
            logger.warning("Bibliotecas para análise de áudio não encontradas. Usando simulação.")
            return self.simulate_emotion_analysis(audio_path)
            
        except Exception as e:
            logger.error(f"Erro na análise alternativa de áudio: {e}")
            return self.simulate_emotion_analysis(audio_path)
    
    def simulate_emotion_analysis(self, audio_path):
        """Simula análise emocional quando outras opções não estão disponíveis"""
        # Lista de emoções possíveis
        primary_emotions = ['neutro', 'hesitação', 'tensão', 'ansiedade', 'frustração', 
                           'entusiasmo', 'confiança', 'tristeza', 'contentamento']
        
        # Usar o nome do arquivo para gerar resultado consistente para o mesmo áudio
        import hashlib
        hash_val = int(hashlib.md5(os.path.basename(audio_path).encode()).hexdigest(), 16)
        
        # Selecionar emoção primária
        primary_idx = hash_val % len(primary_emotions)
        primary = primary_emotions[primary_idx]
        
        # Possivelmente adicionar emoção secundária
        secondary_idx = (hash_val // 100) % len(primary_emotions)
        emotions = [primary]
        
        if secondary_idx != primary_idx and hash_val % 3 == 0:
            emotions.append(primary_emotions[secondary_idx])
        
        # Gerar parâmetros emocionais
        intensity = (hash_val % 10) + 1  # 1-10
        valence = ((hash_val % 100) / 10)  # 0-10
        arousal = (((hash_val // 10) % 100) / 10)  # 0-10
        tension = (((hash_val // 1000) % 100) / 10)  # 0-10
        authenticity = (hash_val % 30) + 70  # 70-99%
        
        return {
            'primary_emotion': primary,
            'emotional_blend': " + ".join(emotions),
            'intensity': intensity,
            'valence': valence,
            'arousal': arousal,
            'tension': tension,
            'authenticity': authenticity,
            'emotions': emotions,
            'simulated': True
        }
    
    def process_image_file(self, message, image_path):
        """Processa um arquivo de imagem"""
        # Implementação simplificada - apenas marca como processado
        return True
    
    def process_video_file(self, message, video_path):
        """Processa um arquivo de vídeo"""
        # Implementação simplificada - apenas marca como processado
        return True
    
    def analyze_conversation(self, conversation, progress_callback=None):
        """Realiza análise completa da conversa"""
        total_messages = len(conversation)
        processed = 0
        
        # Identificar mensagens do perfil alvo
        target_messages = [msg for msg in conversation if msg['is_target']]
        logger.info(f"Analisando {len(target_messages)} mensagens do perfil alvo de {total_messages} totais")
        
        # Análise de contexto para toda a conversa
        conversation_context = self.analyze_conversation_context(conversation)
        
        # Processar cada mensagem do alvo
        for i, msg in enumerate(conversation):
            # Pular mensagens que não são do alvo, exceto para contexto
            if not msg['is_target']:
                # Adicionar contexto mínimo para mensagens que não são do alvo
                self.add_context_to_message(msg, conversation, i, minimal=True)
                continue
            
            # Obter texto para análise
            text = msg['transcription'] if msg['content_type'] == 'audio' and msg['transcription'] else msg['content']
            
            # Adicionar contexto da conversa
            self.add_context_to_message(msg, conversation, i)
            
            # Análise linguística
            msg['analysis']['linguistic_analysis'] = self.analyze_text_linguistics(text)
            
            # Análise de atitude
            msg['analysis']['attitude'] = self.classify_attitude(text, msg)
            
            # Identificação de temas
            msg['analysis']['themes'] = self.identify_themes(text)
            
            # Análise comportamental
            msg['analysis']['behavioral_indicators'] = self.analyze_behavioral_patterns(text, msg)
            
            # Análise psicológica
            msg['analysis']['psychological_indicators'] = self.analyze_psychological_patterns(text, msg)
            
            # Atualizar progresso
            processed += 1
            if progress_callback:
                progress_callback(processed / len(target_messages))
        
        # Análise cruzada e identificação de padrões gerais
        analysis_summary = self.generate_analysis_summary(conversation, conversation_context)
        
        logger.info("Análise de conversa concluída")
        return conversation, analysis_summary
    
    def add_context_to_message(self, message, conversation, message_index, minimal=False):
        """Adiciona informações de contexto a uma mensagem"""
        # Determinar janela de contexto
        context_size = self.config["CONTEXT_WINDOW_SIZE"]
        start_idx = max(0, message_index - context_size)
        
        # Coletar mensagens anteriores para contexto
        previous_messages = []
        for i in range(start_idx, message_index):
            prev_msg = conversation[i]
            prev_text = prev_msg['transcription'] if prev_msg['content_type'] == 'audio' and prev_msg['transcription'] else prev_msg['content']
            
            previous_messages.append({
                'id': prev_msg['id'],
                'author': prev_msg['author'],
                'content': prev_text,
                'timestamp': prev_msg['timestamp'],
                'is_target': prev_msg['is_target']
            })
        
        message['context']['previous_messages'] = previous_messages
        
        # Para mensagens que não são do alvo, não precisamos de contexto adicional
        if minimal:
            return
        
        # Determinar estado da conversa
        if previous_messages:
            # Verificar se a mensagem atual é uma resposta
            is_response = not previous_messages[-1]['is_target']
            
            # Calcular tempo de resposta se for uma resposta
            response_time = None
            if is_response:
                prev_timestamp = previous_messages[-1]['timestamp']
                current_timestamp = message['timestamp']
                response_time = (current_timestamp - prev_timestamp) / 60  # minutos
            
            # Determinar estado (iniciando conversa, respondendo, continuando)
            if not previous_messages:
                conversation_state = "iniciando"
            elif is_response:
                conversation_state = "respondendo"
            else:
                conversation_state = "continuando"
            
            message['context']['conversation_state'] = {
                'state': conversation_state,
                'is_response': is_response,
                'response_time': response_time,
                'previous_topic': self.identify_main_topic(previous_messages)
            }
    
    def identify_main_topic(self, messages):
        """Identifica o tópico principal de uma sequência de mensagens"""
        if not messages:
            return None
        
        # Coletar todos os temas mencionados
        all_themes = []
        for msg in messages:
            if isinstance(msg, dict) and 'content' in msg:
                themes = self.identify_themes(msg['content'])
                all_themes.extend(themes)
        
        # Se não houver temas identificados
        if not all_themes:
            return None
        
        # Contar ocorrências
        theme_counter = Counter(all_themes)
        
        # Retornar o tema mais comum
        return theme_counter.most_common(1)[0][0]
    
    def analyze_conversation_context(self, conversation):
        """Analisa o contexto geral da conversa"""
        # Extrair informações básicas
        total_messages = len(conversation)
        target_messages = [msg for msg in conversation if msg['is_target']]
        user_messages = [msg for msg in conversation if not msg['is_target']]
        
        # Calcular estatísticas básicas
        message_ratio = len(target_messages) / total_messages if total_messages > 0 else 0
        
        # Calcular média de palavras por mensagem
        target_word_counts = []
        for msg in target_messages:
            text = msg['transcription'] if msg['content_type'] == 'audio' and msg['transcription'] else msg['content']
            word_count = len(text.split())
            target_word_counts.append(word_count)
        
        avg_words_per_message = sum(target_word_counts) / len(target_word_counts) if target_word_counts else 0
        
        # Calcular tempos de resposta
        response_times = []
        for i in range(1, len(conversation)):
            curr_msg = conversation[i]
            prev_msg = conversation[i-1]
            
            # Se a mensagem atual é do alvo e a anterior não é
            if curr_msg['is_target'] and not prev_msg['is_target']:
                time_diff = datetime.fromisoformat(curr_msg['datetime']) - datetime.fromisoformat(prev_msg['datetime'])
                response_times.append(time_diff.total_seconds() / 60)  # minutos
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Determinar janela temporal da conversa
        if conversation:
            start_time = datetime.fromisoformat(conversation[0]['datetime'])
            end_time = datetime.fromisoformat(conversation[-1]['datetime'])
            duration = (end_time - start_time).total_seconds() / 3600  # horas
        else:
            start_time = None
            end_time = None
            duration = None
        
        # Identificar distribuição de tipos de conteúdo
        content_types = Counter([msg['content_type'] for msg in target_messages])
        
        # Construir objeto de contexto
        context = {
            'total_messages': total_messages,
            'target_messages': len(target_messages),
            'user_messages': len(user_messages),
            'message_ratio': message_ratio,
            'avg_words_per_message': avg_words_per_message,
            'avg_response_time': avg_response_time,
            'content_type_distribution': dict(content_types),
            'temporal_window': {
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'duration_hours': duration
            }
        }
        
        return context
    
    def analyze_text_linguistics(self, text):
        """Realiza análise linguística do texto"""
        # Análise básica
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_word_length = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0
        
        # Detecção de formalidade
        formal_indicators = ['conforme', 'solicito', 'informo', 'cordialmente', 'atenciosamente', 
                           'prezado', 'senhor', 'senhora', 'doutor', 'doutora']
        informal_indicators = ['oi', 'olá', 'beleza', 'valeu', 'blz', 'tranquilo', 'cara', 'mano', 'véi']
        
        formal_count = sum(1 for word in formal_indicators if word in text.lower())
        informal_count = sum(1 for word in informal_indicators if word in text.lower())
        
        formality_score = (formal_count - informal_count) / (formal_count + informal_count + 1)
        formality_score = max(-1, min(1, formality_score))  # Normalizar entre -1 e 1
        
        # Detecção de complexidade
        complex_structures = ['entretanto', 'portanto', 'consequentemente', 'ademais', 'conquanto',
                             'à medida que', 'tendo em vista', 'em virtude de', 'não obstante']
        complex_count = sum(1 for phrase in complex_structures if phrase in text.lower())
        
        complexity_score = min(1.0, (avg_word_length / 8) + (complex_count / 5) + (sentence_count / 10))
        
        # Detecção de tom
        positive_words = ['bom', 'ótimo', 'excelente', 'feliz', 'satisfeito', 'grato', 'obrigado',
                         'agradeço', 'perfeito', 'maravilhoso', 'sim', 'claro', 'concordo']
        negative_words = ['ruim', 'péssimo', 'infelizmente', 'triste', 'insatisfeito', 'problema',
                         'erro', 'falha', 'desculpe', 'não', 'nunca', 'jamais', 'discordo']
        neutral_words = ['ok', 'bem', 'talvez', 'possivelmente', 'provavelmente', 'entendo']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        neutral_count = sum(1 for word in neutral_words if word in text.lower())
        
        # Determinar tom predominante
        if positive_count > negative_count and positive_count > neutral_count:
            tone = "positivo"
        elif negative_count > positive_count and negative_count > neutral_count:
            tone = "negativo"
        else:
            tone = "neutro"
        
        # Detectar hedging (linguagem evasiva/hesitante)
        hedging_phrases = ['eu acho', 'talvez', 'possivelmente', 'provavelmente', 'aparentemente',
                          'não tenho certeza', 'não sei', 'pode ser', 'quem sabe', 'vou ver']
        hedging_count = sum(1 for phrase in hedging_phrases if phrase in text.lower())
        hedging_score = min(1.0, hedging_count / 3)
        
        # Resultado da análise
        analysis = {
            'basic_metrics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_word_length': round(avg_word_length, 2)
            },
            'style_metrics': {
                'formality': round(formality_score, 2),
                'complexity': round(complexity_score, 2),
                'hedging': round(hedging_score, 2)
            },
            'tone': {
                'primary_tone': tone,
                'positive_score': round(positive_count / (word_count * 0.1) if word_count > 0 else 0, 2),
                'negative_score': round(negative_count / (word_count * 0.1) if word_count > 0 else 0, 2),
                'neutral_score': round(neutral_count / (word_count * 0.1) if word_count > 0 else 0, 2)
            }
        }
        
        return analysis
    
    def classify_attitude(self, text, message):
        """Classifica a atitude expressa na mensagem"""
        text = text.lower()
        
        # Categorias de atitude
        attitude_indicators = {
            'evasiva': [
                "vou ver", "depois te falo", "talvez", "quem sabe", "não sei",
                "pode ser", "vamos ver", "entendi", "tá", "tá bom", "aham",
                "depois eu vejo", "vou analisar", "preciso verificar"
            ],
            'submissa': [
                "como você quiser", "se você preferir", "como achar melhor",
                "às suas ordens", "o que você decidir", "sim senhor", "sim senhora",
                "se você acha melhor", "como o senhor preferir", "faço como pedir"
            ],
            'colaborativa': [
                "vou resolver", "já providenciei", "posso ajudar", "vamos resolver",
                "podemos fazer", "vou dar um jeito", "sem problema", "certamente",
                "claro", "vou cuidar disso", "como podemos resolver", "estou à disposição"
            ],
            'resistente': [
                "não dá", "impossível", "difícil", "complicado", "não posso",
                "infelizmente", "não tenho como", "é difícil", "não sei se consigo",
                "não é possível", "está fora do meu alcance", "não depende de mim"
            ],
            'autoritária': [
                "você deve", "é necessário", "obrigatório", "tem que",
                "exijo", "precisa ser", "faça", "não tem escolha",
                "é uma ordem", "não aceito", "não é opcional", "determino que"
            ],
            'defensiva': [
                "não foi minha culpa", "eu não sabia", "ninguém me avisou",
                "não me responsabilizo", "não era minha função", "eu avisei",
                "já tinha dito", "não é minha responsabilidade", "fizeram sem me consultar"
            ]
        }
        
        # Contar ocorrências de indicadores
        attitude_scores = {}
        for attitude, indicators in attitude_indicators.items():
            count = sum(1 for phrase in indicators if phrase in text)
            attitude_scores[attitude] = count
        
        # Incorporar informações de emoção do áudio (se disponível)
        if message['content_type'] == 'audio' and message['analysis']['emotion']:
            emotion = message['analysis']['emotion']
            primary_emotion = emotion.get('primary_emotion', '')
            
            # Ajustar pontuações com base na emoção
            if primary_emotion == 'hesitação':
                attitude_scores['evasiva'] += 1
            elif primary_emotion == 'tensão':
                attitude_scores['defensiva'] += 0.5
                attitude_scores['resistente'] += 0.5
            elif primary_emotion == 'confiança':
                attitude_scores['autoritária'] += 0.5
                attitude_scores['colaborativa'] += 0.5
            elif primary_emotion == 'ansiedade':
                attitude_scores['evasiva'] += 0.5
                attitude_scores['submissa'] += 0.5
        
        # Determinar a atitude predominante
        max_score = max(attitude_scores.values()) if attitude_scores else 0
        
        if max_score > 0:
            # Lista de atitudes com a pontuação máxima
            primary_attitudes = [attitude for attitude, score in attitude_scores.items() if score == max_score]
            primary_attitude = primary_attitudes[0]  # Pegar a primeira se houver empate
        else:
            # Analisar com base em características linguísticas
            linguistic = message['analysis'].get('linguistic_analysis', {})
            
            if linguistic:
                formality = linguistic.get('style_metrics', {}).get('formality', 0)
                hedging = linguistic.get('style_metrics', {}).get('hedging', 0)
                tone = linguistic.get('tone', {}).get('primary_tone', 'neutro')
                
                if hedging > 0.5:
                    primary_attitude = 'evasiva'
                elif formality > 0.5 and tone == 'positivo':
                    primary_attitude = 'colaborativa'
                elif formality < -0.3 and tone == 'negativo':
                    primary_attitude = 'resistente'
                elif formality > 0.7:
                    primary_attitude = 'formal'
                else:
                    primary_attitude = 'neutra'
            else:
                primary_attitude = 'neutra'
        
        # Calcular força da atitude (0-10)
        if max_score > 0:
            attitude_strength = min(10, max_score * 3)
        else:
            attitude_strength = 3  # Valor médio-baixo para atitudes inferidas indiretamente
        
        # Criar resultado detalhado
        result = {
            'primary_attitude': primary_attitude,
            'strength': round(attitude_strength, 1),
            'scores': {k: round(v, 2) for k, v in attitude_scores.items() if v > 0}
        }
        
        return result
    
    def identify_themes(self, text):
        """Identifica os temas discutidos na mensagem"""
        text = text.lower()
        
        # Dicionário de temas com palavras-chave associadas
        theme_keywords = {
            "plantao": [
                "plantão", "escala", "horário", "paciente", "atender", "atendimento", 
                "consulta", "agendamento", "médico", "triagem", "emergência", "hospital",
                "pronto-socorro", "UBS", "posto", "clínica"
            ],
            "feriado": [
                "feriado", "folga", "recesso", "ponto facultativo", "descanso", 
                "compensação", "emenda", "ausência", "férias", "licença"
            ],
            "pagamento": [
                "nota fiscal", "pagamento", "honorário", "depósito", "remuneração", 
                "valor", "contrato", "imposto", "tributação", "recibo", "salário",
                "dinheiro", "pagar", "receber", "conta", "banco", "transferência"
            ],
            "reuniao": [
                "reunião", "conversa", "discutir", "encontro", "alinhamento", 
                "discussão", "debate", "pauta", "comitê", "equipe", "presencial",
                "virtual", "online", "zoom", "teams", "meet"
            ],
            "documentacao": [
                "documento", "assinatura", "papel", "formulário", "registro", 
                "prontuário", "certificado", "atestado", "declaração", "relatório",
                "laudo", "receita", "prescrição", "encaminhamento", "requisição"
            ],
            "problema": [
                "problema", "dificuldade", "erro", "falha", "conflito", "reclamação",
                "queixa", "insatisfação", "quebra", "defeito", "emergência", "urgência",
                "crítico", "grave", "complicado", "impossível"
            ],
            "pessoal": [
                "família", "filho", "filha", "marido", "esposa", "pai", "mãe",
                "cansado", "doente", "saúde", "pessoal", "casa", "particular",
                "privado", "íntimo", "sentir", "emoção"
            ],
            "reconhecimento": [
                "obrigado", "agradeço", "elogio", "parabéns", "excelente", "ótimo",
                "satisfeito", "reconhecer", "valorizar", "mérito", "competência",
                "habilidade", "talento", "dedicação"
            ]
        }
        
        # Detectar temas baseados nas palavras-chave
        detected_themes = []
        
        for theme, keywords in theme_keywords.items():
            # Verificar presença de palavras-chave
            if any(keyword in text for keyword in keywords):
                detected_themes.append(f"#{theme}")
        
        return detected_themes
    
    def analyze_behavioral_patterns(self, text, message):
        """Analisa padrões comportamentais na mensagem"""
        # Obter contexto e análises já realizadas
        attitude = message.get('analysis', {}).get('attitude', {})
        linguistic = message.get('analysis', {}).get('linguistic_analysis', {})
        emotion = message.get('analysis', {}).get('emotion', {})
        
        # Indicadores comportamentais a detectar
        behavioral_indicators = {}
        
        # 1. Estratégias de evitação
        evasion_indicators = [
            "vou ver", "preciso verificar", "não sei dizer", "vamos pensar", 
            "depois falamos", "mais tarde vejo", "não tenho essa informação"
        ]
        
        evasion_score = sum(1 for phrase in evasion_indicators if phrase in text.lower())
        
        if attitude.get('primary_attitude') == 'evasiva':
            evasion_score += 1
        
        if linguistic.get('style_metrics', {}).get('hedging', 0) > 0.5:
            evasion_score += 1
        
        if emotion.get('primary_emotion') in ['hesitação', 'ansiedade']:
            evasion_score += 1
        
        behavioral_indicators