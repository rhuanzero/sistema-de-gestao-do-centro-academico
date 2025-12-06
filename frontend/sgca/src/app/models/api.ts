// src/app/models/api.models.ts

// --- ENUMS AUXILIARES ---
// Usamos Union Types para facilitar a leitura no HTML

export type Cargo = 'Presidente' | 'Tesoureiro' | 'Coordenador' | 'Membro';
export type TipoTransacao = 'Receita' | 'Despesa';
export type StatusPatrimonio = 'Disponível' | 'Em Uso' | 'Em Manutenção' | 'Baixado';

// --- AUTENTICAÇÃO ---
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  cargo: Cargo;
  centro_academico_id: number;
}

// --- USUÁRIOS (MySQL) ---
export interface Usuario {
  id: number;
  nome: string;
  email: string;
  cpf?: string;
  telefone?: string;
  cargo: Cargo;
  status: string;
  departamento_id?: number;
  centro_academico_id: number;
}

export interface UsuarioCreate extends Omit<Usuario, 'id' | 'status'> {
  senha: string;
}

// --- FINANCEIRO (MySQL) ---
export interface Transacao {
  id: number;
  descricao: string;
  valor: number;
  tipo: TipoTransacao;
  data: string; // O Python envia datetime como string ISO
  usuario_id: number;
  centro_academico_id: number;
  responsavel?: string; // Campo extra que vem no relatório
}

export interface SaldoResponse {
  saldo_atual: number;
  receitas: number;
  despesas: number;
  ultima_atualizacao: string;
}

// --- EVENTOS (MongoDB - IDs são strings) ---
export interface Tarefa {
  id_interno: number;
  descricao: string;
  status: string;
  usuario_responsavel_id: number;
  criado_em?: string;
}

export interface Patrocinio {
  nome_empresa: string;
  tipo: string;
  valor: number;
  contato: string;
  status_pagamento: string;
}

export interface Evento {
  id: string; // MongoDB retorna ObjectId como string
  titulo: string;
  descricao: string;
  local: string;
  data_inicio: string;
  data_fim: string;
  orcamento_limite?: number;
  status: string;
  tarefas?: Tarefa[];
  patrocinios?: Patrocinio[];
  criado_por?: {
    id: string;
    nome: string;
  };
}

// --- COMUNICAÇÃO (MongoDB) ---
export interface Postagem {
  id: string;
  titulo: string;
  conteudo_texto: string;
  midia_destino: string;
  data_agendamento: string;
  status: string; // 'Rascunho', 'Agendado', 'Publicado'
  anexos?: string[];
  autor_id?: number;
}

export interface Documento {
  // Baseado no seu componente visual, já que não vi schema específico no Python
  title: string;
  date: string;
  author: string;
}

// --- PATRIMÔNIO (MongoDB) ---
export interface HistoricoItem {
  timestamp: string;
  usuario_id: number;
  acao: string;
  detalhes: string;
}

export interface Patrimonio {
  id: string;
  nome: string;
  descricao: string;
  status: StatusPatrimonio;
  data_aquisicao: string;
  historico?: HistoricoItem[];
  
  // Campos opcionais que vi no seu HTML mas não estavam explícitos no Schema base
  // Adicionei como opcionais (?) para não quebrar a compilação
  valor?: number; 
  localizacao?: string; 
  condition?: string; // 'Novo', 'Bom', 'Danificado'
}