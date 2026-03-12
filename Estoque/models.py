from django.db import models

class Tecido(models.Model):
  
    nome = models.CharField(max_length=100)   # pode repetir
    cor = models.CharField(max_length=100)    # diferencia
    metragem = models.FloatField()

    class Meta:
        unique_together = ('nome', 'cor')  # garante que a combinação seja única

    preco = models.DecimalField(max_digits=10, decimal_places=2)
    
    
class Encomenda(models.Model):

    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('CONCLUIDA', 'Concluída'),
    ]

    nomeCliente = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    tecidoEscolhido = models.CharField(max_length=100)
    corEscolhida = models.CharField(max_length=50)
    metragem = models.DecimalField(max_digits=8, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True, null=True)
    data_entrega = models.DateField(blank=True, null=True)

    # 🆕 STATUS
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ABERTA'
    )

    def __str__(self):
        return self.nome
