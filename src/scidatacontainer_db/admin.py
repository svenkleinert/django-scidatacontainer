from django.contrib import admin
from guardian.admin import GuardedModelAdmin

# Register your models here.
from scidatacontainer_db.models import ContainerType, DataSet, File, Keyword,\
                                       Software


class ContainerTypeAdmin(admin.ModelAdmin):
    pass


class DataSetAdmin(GuardedModelAdmin):
    pass


class FileAdmin(admin.ModelAdmin):
    pass


class KeywordAdmin(admin.ModelAdmin):
    pass


class SoftwareAdmin(admin.ModelAdmin):
    pass


admin.site.register(ContainerType, ContainerTypeAdmin)
admin.site.register(DataSet, DataSetAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Software, SoftwareAdmin)
