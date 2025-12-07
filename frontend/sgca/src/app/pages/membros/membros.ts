import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // <--- IMPORTANTE PARA O FORMULÁRIO
import { ApiService } from '../../services/apiservice';

@Component({
  selector: 'app-membros',
  standalone: true,
  imports: [CommonModule, FormsModule], // <--- Adicione FormsModule aqui
  templateUrl: './membros.html',
  styleUrls: ['./membros.css']
})
export class Membros implements OnInit {

  membros: any[] = [];
  carregando = false;
  
  // Controle do Modal
  mostrarModal = false;
  
  // Objeto temporário para o formulário
  membroForm: any = {
    id: null,
    nome: '',
    email: '',
    cpf: '',
    telefone: '',
    cargo: 'Membro', // Valor padrão
    departamento_id: null,
    centro_academico_id: 1 // Ajuste conforme seu sistema
  };

  constructor(
    private apiService: ApiService,
    private cd: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.carregarMembros();
  }

  carregarMembros() {
    this.carregando = true;
    this.apiService.getMembers().subscribe({
      next: (dados) => {
        this.membros = dados;
        this.carregando = false;
        this.cd.detectChanges();
      },
      error: (e) => console.error(e)
    });
  }

  // --- AÇÕES DO MODAL ---
  
abrirModalCriacao() {
    this.membroForm = { 
      id: null, 
      nome: '', 
      email: '', 
      cpf: '', 
      telefone: '', 
      cargo: 'Membro', 
      centro_academico_id: 1,
      senha: '' // <--- ADICIONE ISSO AQUI! O Backend exige senha para criar.
    };
    this.mostrarModal = true;
  }

  abrirModalEdicao(membro: any) {
    // Copia os dados do membro clicado para o formulário (sem mexer na tabela ainda)
    this.membroForm = { ...membro }; 
    this.mostrarModal = true;
  }

  fecharModal() {
    this.mostrarModal = false;
  }

 salvar() {
    // 1. PREPARAÇÃO DOS DADOS (Cópia e Limpeza)
    const dadosParaEnviar = { ...this.membroForm };

    if (!dadosParaEnviar.cpf) dadosParaEnviar.cpf = null;
    if (!dadosParaEnviar.telefone) dadosParaEnviar.telefone = null;
    if (!dadosParaEnviar.departamento_id) dadosParaEnviar.departamento_id = null;
    dadosParaEnviar.centro_academico_id = Number(dadosParaEnviar.centro_academico_id);

    // Validação de Senha para novos membros
    if (!dadosParaEnviar.id && !dadosParaEnviar.senha) {
        alert("⚠️ A senha é obrigatória!");
        return;
    }
    // Remove senha vazia na edição
    if (dadosParaEnviar.id && !dadosParaEnviar.senha) {
        delete dadosParaEnviar.senha;
    }

    // 2. ENVIO PARA API
    if (this.membroForm.id) {
      // --- EDIÇÃO ---
      this.apiService.updateMember(this.membroForm.id, dadosParaEnviar).subscribe({
        next: () => {
          // alert('Membro atualizado!'); <--- REMOVEMOS ISSO
          this.fecharModal();      // 1º Fecha a janela
          this.carregarMembros();  // 2º Atualiza a tabela no fundo
        },
        error: (e) => {
          console.error(e);
          alert('Erro ao editar: ' + (e.error.detail || e.message));
        }
      });
    } else {
      // --- CRIAÇÃO ---
      this.apiService.createMember(dadosParaEnviar).subscribe({
        next: () => {
          // alert('Membro criado!'); <--- REMOVEMOS ISSO TAMBÉM
          this.fecharModal();      // 1º Fecha a janela na hora
          this.carregarMembros();  // 2º A tabela recarrega sozinha
        },
        error: (e) => {
          console.error(e);
          const msg = e.error.detail ? JSON.stringify(e.error.detail) : e.message;
          alert('Erro ao criar: ' + msg);
        }
      });
    }
  }

// Adicione isso DENTRO da classe MembrosComponent, antes do último }

  excluir(membro: any) {
    if (confirm(`Tem certeza que deseja excluir ${membro.nome}?`)) {
      
      this.apiService.deleteMember(membro.id).subscribe({
        next: () => {
          // 1. REMOÇÃO VISUAL IMEDIATA (O Pulo do Gato 🐱)
          // Filtra a lista mantendo apenas quem tem ID diferente do excluído
          this.membros = this.membros.filter(m => m.id !== membro.id);
          
          // 2. Força o Angular a repintar a tabela agora
          this.cd.detectChanges();
          
          // (Opcional) Só pra garantir a sincronia total, busca do banco em background
          // this.carregarMembros(); 
        },
        error: (e) => {
          console.error(e);
          const msg = e.error.detail || e.message;
          alert('Erro ao excluir: ' + msg);
        }
      });
    }
  }
}