from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tecidos/', views.lista_tecidos, name='lista_tecidos'),
    path('tecidos/cadastro/', views.cadastro_tecido, name='cadastro_tecido'),
    path('tecidos/<int:tecido_id>/editar/', views.editar_tecido, name='editar_tecido'),
    path('tecidos/<int:tecido_id>/deletar/', views.deletar_tecido, name='deletar_tecido'),

    path('encomendas/', views.listar_encomendas, name='listar_encomendas'),
    path('encomendas/cadastro/', views.registrar_encomenda, name='registrar_encomenda'),
    path('encomenda/editar/<int:encomenda_id>/', views.editar_encomenda, name='editar_encomenda'),
    path('encomendas/<int:encomenda_id>/deletar/', views.deletar_encomenda, name='deletar_encomenda'),
    path('encomenda/concluir/<int:encomenda_id>/', views.concluir_encomenda, name='concluir_encomenda'),

]
