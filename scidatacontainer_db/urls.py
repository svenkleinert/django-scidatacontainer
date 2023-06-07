from django.urls import include, path

from rest_framework import routers

from . import views
from . import api_views

router = routers.DefaultRouter()
router.register(r"datasets", api_views.DataSetViewSet, basename="dataset")
router.register(r"container-types", api_views.ContainerTypeViewSet,
                basename="containertype")
router.register(r"files", api_views.FileViewSet, basename="file")
router.register(r"keywords", api_views.KeywordViewSet, basename="keyword")
router.register(r"softwares", api_views.SoftwareViewSet, basename="software")

app_name = "scidatacontainer_db"
urlpatterns = [
    path('', views.IndexView.as_view(), name='ui-index'),
    path('login/', views.LoginView.as_view(), name='ui-login'),
    path('logout/', views.LogoutView.as_view(), name='ui-logout'),
    path('<uuid:pk>/permissions/', views.UpdatePermissionsView.as_view(),
         name='ui-permission_update'),
    path('<uuid:pk>/delete/', views.InvalidationView.as_view(),
         name='ui-delete'),
    path('<uuid:pk>/', views.DetailView.as_view(), name='ui-detail'),
    path('upload/', views.UploadFileView.as_view(), name='ui-fileupload'),
    path('download/<uuid:pk>', views.DownloadFileView.as_view(),
         name='ui-filedownload'),
    path('keys/', views.ApiKeyView.as_view(), name='ui-keys'),
    path('api/', include((router.urls, app_name), namespace="api")),
]
