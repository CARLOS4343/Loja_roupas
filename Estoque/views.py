from datetime import datetime, timedelta
from django.shortcuts import redirect, render
from django.db.models import Sum, DecimalField
from django.db.models import F
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from Estoque.models import Encomenda, Tecido
from django.utils import timezone   # ✅ certo



# Create your views here.
def home(request):
    hoje = timezone.now().date()
    limite = hoje + timedelta(days=7)

    total_tecidos = Tecido.objects.count()

    total_encomendas = Encomenda.objects.filter(
        status='ABERTA'
    ).count()

    valor_total_estoque = Tecido.objects.aggregate(
        total_valor=Sum(F('metragem') * F('preco'), output_field=DecimalField())
    )['total_valor'] or 0

    valor_total_encomendas = Encomenda.objects.filter(
        status='ABERTA'
    ).aggregate(
        total_valor=Sum('price', output_field=DecimalField())
    )['total_valor'] or 0

    #  Encomendas atrasadas
    encomendas_atrasadas = Encomenda.objects.filter(
        data_entrega__isnull=False,
        data_entrega__lt=hoje,
        status='ABERTA'
    )

    #  Encomendas próximas do prazo
    encomendas_proximas = Encomenda.objects.filter(
        data_entrega__isnull=False,
        data_entrega__range=(hoje, limite),
        status='ABERTA'
    )

    context = {
        'total_tecidos': total_tecidos,
        'total_encomendas': total_encomendas,
        'valor_total_estoque': valor_total_estoque,
        'valor_total_encomendas': valor_total_encomendas,
        'count_proximas': encomendas_proximas.count(),
        'count_atrasadas': encomendas_atrasadas.count(),
    }

    return render(request, 'estoque/home.html', context)
def cadastro_tecido(request):
    if request.method == 'POST':
        
        Tecido.objects.create( 
            nome=request.POST.get('nome'),
            metragem=request.POST.get('metragem'),
            preco=request.POST.get('preco'),
            cor=request.POST.get('cor'),
        ) 
           
            
        return redirect('home')
    tecidos = Tecido.objects.all()
    return render(request, 'estoque/cadastro_tecido.html', {'tecidos': tecidos})


def lista_tecidos(request):
    nome = request.GET.get('nome')
    cor = request.GET.get('cor')

    tecidos = Tecido.objects.all()

    if nome:
        tecidos = tecidos.filter(nome__icontains=nome)

    if cor:
        tecidos = tecidos.filter(cor__icontains=cor)

    context = {
        'tecidos': tecidos
    }

    return render(request, 'estoque/lista_tecidos.html', context)

def editar_tecido(request, tecido_id):
    tecido = Tecido.objects.get(id=tecido_id)
    if request.method == 'POST':
        tecido.nome = request.POST.get('nome')
        tecido.metragem = request.POST.get('metragem')
        tecido.preco = request.POST.get('preco')
        tecido.cor = request.POST.get('cor')
        tecido.save()
        return redirect('lista_tecidos')
    return render(request, 'estoque/editar_tecido.html', {'tecido': tecido})

def deletar_tecido(request, tecido_id):
    tecido = Tecido.objects.get(id=tecido_id)
    tecido.delete()
    return redirect('estoque/lista_tecidos')


def registrar_encomenda(request):
    if request.method == 'POST':
        nome_cliente = request.POST.get('nomeCliente')
        modelo = request.POST.get('modelo')
        tecido_escolhido_nome = request.POST.get('tecidoEscolhido')
        cor_escolhida = request.POST.get('corEscolhida')
        metragem_str = request.POST.get('metragem')
        descricao = request.POST.get('descricao')
        price_str = request.POST.get('price')
        data_entrega_str = request.POST.get('data_entrega')

        try:
            tecido_obj = Tecido.objects.get(
                nome=tecido_escolhido_nome,
                cor=cor_escolhida
            )
        except Tecido.DoesNotExist:
            messages.error(request, "Tecido não encontrado no estoque.")
            return redirect('registrar_encomenda')

        # Conversões seguras
        try:
            metragem = Decimal(metragem_str)
            price = Decimal(price_str)
        except (InvalidOperation, TypeError):
            messages.error(request, "Valores inválidos de metragem ou preço.")
            return redirect('registrar_encomenda')

        # Verifica se há estoque suficiente
        if tecido_obj.metragem < metragem:
            messages.error(request, "Metragem solicitada maior que o estoque disponível.")
            return redirect('registrar_encomenda')

        # Calcula preço mínimo permitido
        preco_minimo = metragem * tecido_obj.preco

        # Valida o preço informado
        if price < preco_minimo:
            messages.error(
                request,
                f"Atenção Preço abaixo do custo! \n O preço mínimo para essa encomenda é R$ {preco_minimo:.2f}"
            )
            return redirect('registrar_encomenda')

        # Converte a data de entrega (se enviada)
        data_entrega = None
        if data_entrega_str:
            try:
                data_entrega = datetime.strptime(data_entrega_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Data de entrega inválida.")
                return redirect('registrar_encomenda')

        # Cria a encomenda com o campo correto
        Encomenda.objects.create(
            nomeCliente=nome_cliente,
            modelo=modelo,
            tecidoEscolhido=tecido_escolhido_nome,
            corEscolhida=cor_escolhida,
            metragem=metragem,
            descricao=descricao,
            price=price,
            data_entrega=data_entrega  # ✅ campo correto
        )

        # Atualiza estoque com F() para evitar condições de corrida
        Tecido.objects.filter(id=tecido_obj.id).update(metragem=F('metragem') - metragem)

        return redirect('home')

    return render(request, 'estoque/registrar_encomenda.html')


def listar_encomendas(request):

    hoje = timezone.now().date()
    limite = hoje + timedelta(days=7)

    filtro = request.GET.get('filtro')

    encomendas = Encomenda.objects.all()

    if filtro == 'atrasadas':
        encomendas = encomendas.filter(
            data_entrega__lt=hoje,
            status='ABERTA'
        )

    elif filtro == 'proximas':
        encomendas = encomendas.filter(
            data_entrega__range=(hoje, limite),
            status='ABERTA'
        )

    return render(request, 'estoque/listar_encomendas.html', {
        'encomendas': encomendas
    })

def editar_encomenda(request, encomenda_id):
    encomenda = Encomenda.objects.get(id=encomenda_id)
    if request.method == 'POST':
        encomenda.nomeCliente = request.POST.get('nomeCliente')
        encomenda.modelo = request.POST.get('modelo')
        encomenda.tecidoEscolhido = request.POST.get('tecidoEscolhido')
        encomenda.corEscolhida = request.POST.get('corEscolhida')
        encomenda.metragem = request.POST.get('metragem')
        encomenda.descricao = request.POST.get('descricao')
        encomenda.price = request.POST.get('price')
        encomenda.data_entrega = request.POST.get('data_entrega')
        encomenda.save()
        return redirect('listar_encomendas')
    return render(request, 'estoque/editar_encomenda.html', {'encomenda': encomenda})



def deletar_encomenda(request, encomenda_id):
    try:
        encomenda = Encomenda.objects.get(id=encomenda_id)

        # 🔒 Só devolve metragem se NÃO estiver concluída
        if encomenda.status == 'ABERTA':
            try:
                tecido_obj = Tecido.objects.get(
                    nome=encomenda.tecidoEscolhido,
                    cor=encomenda.corEscolhida
                )

                tecido_obj.metragem = F('metragem') + encomenda.metragem
                tecido_obj.save(update_fields=['metragem'])

            except Tecido.DoesNotExist:
                messages.error(request, "Tecido da encomenda não encontrado no estoque.")

        encomenda.delete()

    except Encomenda.DoesNotExist:
        messages.error(request, "Encomenda não encontrada.")

    return redirect('listar_encomendas')


def editar_encomenda(request, encomenda_id):
    encomenda = Encomenda.objects.get(id=encomenda_id)
    if request.method == 'POST':
        encomenda.nomeCliente = request.POST.get('nomeCliente')
        encomenda.modelo = request.POST.get('modelo')
        encomenda.tecidoEscolhido = request.POST.get('tecidoEscolhido')
        encomenda.corEscolhida = request.POST.get('corEscolhida')
        encomenda.metragem = request.POST.get('metragem')
        encomenda.price = request.POST.get('price')
        encomenda.save()
        return redirect('listar_encomendas')
    return render(request, 'estoque/editar_encomenda.html', {'encomenda': encomenda})

def concluir_encomenda(request, encomenda_id):
    encomenda = Encomenda.objects.get(id=encomenda_id)
    encomenda.status = 'CONCLUIDA'
    encomenda.save()
    return redirect('listar_encomendas')
def prazo_encomenda(request, encomenda_id):
    # Lógica para calcular e exibir as encomendas próximas do prazo de entrega
    encomenda = Encomenda.objects.get(id=encomenda_id)
    prazo_entrega = encomenda.data_entrega - timezone.now()
    if prazo_entrega.days < 0:
        messages.warning(request, "A encomenda está atrasada!")
    elif prazo_entrega.days < 7:
        messages.info(request, "A encomenda está próxima do prazo de entrega.")
    return redirect('listar_encomendas')
