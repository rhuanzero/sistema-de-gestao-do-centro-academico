import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/apiservice';

@Component({
  selector: 'app-financeiro',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './financeiro.html',
  styleUrls: ['./financeiro.css']
})
export class Financeiro implements OnInit {

  // 🔴 CORREÇÃO 1: Use 'any' aqui para evitar o erro TS2739
  saldo: any = { 
    saldo_atual: 0, 
    receitas: 0, 
    despesas: 0 
  };

  transacoes: any[] = [];
  carregando = false;
  mostrarModal = false;

  novaTransacao = { 
    descricao: '', 
    valor: 0, 
    tipo: 'Receita'
  };

  constructor(
    private apiService: ApiService,
    private cd: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.carregarDados();
  }

  carregarDados() {
    this.carregando = true;

    // Busca Saldo
    this.apiService.getBalance().subscribe({
      next: (dados: any) => { // 🔴 Use ': any' explícito
        this.saldo = dados;
        this.cd.detectChanges();
      },
      error: (e: any) => console.error('Erro saldo:', e) // 🔴 Use ': any'
    });

    // Busca Extrato
    this.apiService.getTransactions().subscribe({
      next: (lista: any[]) => { // 🔴 Use ': any[]'
        this.transacoes = lista;
        this.carregando = false;
        this.cd.detectChanges();
      },
      error: (e: any) => { // 🔴 Use ': any'
        console.error('Erro extrato:', e);
        this.carregando = false;
      }
    });
  }

  abrirModal() {
    this.novaTransacao = { descricao: '', valor: 0, tipo: 'Receita' };
    this.mostrarModal = true;
  }

  fecharModal() {
    this.mostrarModal = false;
  }

  salvar() {
    if (!this.novaTransacao.descricao || this.novaTransacao.valor <= 0) {
      alert('Preencha a descrição e valor > 0');
      return;
    }

    const payload = {
      descricao: this.novaTransacao.descricao,
      valor: Number(this.novaTransacao.valor),
      tipo: this.novaTransacao.tipo,
      data: new Date().toISOString() 
    };

    // Agora o createTransaction existe no service!
    this.apiService.createTransaction(payload).subscribe({
      next: (resposta: any) => { // 🔴 CORREÇÃO 2: Adicionado ': any'
        alert('Lançamento realizado!');
        this.fecharModal();
        this.carregarDados();
      },
      error: (e: any) => { // 🔴 CORREÇÃO 3: Adicionado ': any'
        console.error(e);
        const msg = e.error?.detail ? JSON.stringify(e.error.detail) : e.message;
        alert('Erro: ' + msg);
      }
    });
  }
}