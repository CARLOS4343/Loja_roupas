from django.shortcuts import redirect, render
from django.db.models import Sum, DecimalField
from django.db.models import F
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from Estoque.models import Encomenda, Tecido


# Create your views here.
def home(request):
    total_tecidos = Tecido.objects.count()
    total_encomendas = Encomenda.objects.filter(status='ABERTA').count()
    valor_total_estoque = Tecido.objects.aggregate(
        total_valor=Sum(F('metragem') * F('preco'), output_field=DecimalField())
    )['total_valor'] or 0
    valor_total_encomendas = Encomenda.objects.filter(
        status='ABERTA'
    ).aggregate(
        total_valor=Sum('price', output_field=DecimalField())
    )['total_valor'] or 0

    context={
        'total_tecidos': total_tecidos,
        'total_encomendas': total_encomendas,
        'valor_total_estoque': valor_total_estoque,
        'valor_total_encomendas': valor_total_encomendas,
    }
    return render(request, 'estoque/home.html' , context)

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

        # Cria a encomenda
        Encomenda.objects.create(
            nomeCliente=nome_cliente,
            modelo=modelo,
            tecidoEscolhido=tecido_escolhido_nome,
            corEscolhida=cor_escolhida,
            metragem=metragem,
            descricao=descricao,
            price=price,
        )

        # Atualiza estoque com F() para evitar condições de corrida
        Tecido.objects.filter(id=tecido_obj.id).update(metragem=F('metragem') - metragem)

        return redirect('home')

    return render(request, 'estoque/registrar_encomenda.html')


def listar_encomendas(request):
    encomendas = Encomenda.objects.all()
    return render(request, 'estoque/listar_encomendas.html', {'encomendas': encomendas})

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
