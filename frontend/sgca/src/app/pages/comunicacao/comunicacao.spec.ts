import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Comunicacao } from './comunicacao';

describe('Comunicacao', () => {
  let component: Comunicacao;
  let fixture: ComponentFixture<Comunicacao>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Comunicacao]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Comunicacao);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
