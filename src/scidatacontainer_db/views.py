from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
import django.contrib.auth.views as authviews
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, FileResponse,\
                        HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.views import generic

from knox.models import AuthToken
from guardian.shortcuts import get_objects_for_user, remove_perm, assign_perm

from .models import DataSet
from .parsers import parse_container_file
from .utils import ensure_read_permission, ensure_owner, MetaDBError


def _http_response(msg, status_code):
    r = HttpResponse(msg)
    r.status_code = status_code
    r.reason_phrase = msg
    return r


class UploadFileView(LoginRequiredMixin, generic.View):
    """
    Upload a file and parse its content.
    """
    def post(self, request):
        if len(request.FILES) > 0:
            try:
                parse_container_file(request.FILES["uploadfile"], request.user)
            except MetaDBError as e:
                return _http_response(e.args[0]["msg"],
                                      e.args[0]["error_code"])
            return _http_response("Upload successful!", 201)
        return _http_response("No data file found!", 400)


class DownloadFileView(LoginRequiredMixin, generic.DetailView):
    """
    Provide a ::model::`scidatacontainer_db.DataSet` as a FileResponse.
    """
    model = DataSet

    def get(self, request, pk):
        dataset = get_object_or_404(DataSet, id=pk)
        ensure_read_permission(request.user, dataset)

        return FileResponse(open(dataset.server_path, 'rb'))


class IndexView(LoginRequiredMixin, generic.ListView):
    """
    Display a list of :model:`scidatacontainer_db.DataSet`


    **Template**
    :template:`scidatacontainer_db/index.html`
    """
    paginate_by = 20
    model = DataSet
    template_name = 'scidatacontainer_db/index.html'

    def get_queryset(self):
        """
        Get the list of :model:`scidatacontainer_db.DataSet` objects to
        display. It only provides :model:`scidatacontainer_db.DataSet` objects
        that the user is allowed to read and filters for the search query.
        """
        search = self.request.GET.get("search", False)
        q = get_objects_for_user(self.request.user,
                                 "view_dataset",
                                 DataSet) |\
            get_objects_for_user(self.request.user,
                                 "change_dataset",
                                 DataSet) |\
            self.request.user.owner_of.all()

        q = q.filter(valid=True, _replaced_by_field=None)
        if search:
            q_filt = q.filter(
                              Q(id__icontains=search) |
                              Q(id__icontains=search) |
                              Q(author__icontains=search) |
                              Q(title__icontains=search) |
                              Q(comment__icontains=search) |
                              Q(description__icontains=search) |
                              Q(email__icontains=search) |
                              Q(container_type__name__icontains=search) |
                              Q(hash__icontains=search)
                             )
        else:
            q_filt = q

        return q_filt.order_by('-upload_time')

    def get_context_data(self, **kwargs):
        """
        Context Data function to enable pagination.
        """
        context = super().get_context_data(**kwargs)
        paginator = context["page_obj"].paginator
        page = self.request.GET.get("page", 1)
        context["page_range"] = paginator.get_elided_page_range(number=page,
                                                                on_each_side=2,
                                                                on_ends=0)
        return context


class DetailView(LoginRequiredMixin, generic.DetailView):
    """
    Display the detailed information of a single
    :model:`scidatacontainer_db.DataSet`.

    **Template**
    :template:`scidatacontainer_db/detail.html`
    """
    model = DataSet
    template_name = 'scidatacontainer_db/detail.html'

    def get(self, request, pk):
        """
        Handle a GET request. If this :model:`scidatacontainer_db:DataSet` is
        marked invalid, a warning message will be shown. If it was replaced by
        a successor :model:`scidatacontainer_db.DataSet`, a warning message
        will be shown and the user is redirected to the successor.
        """
        self.object = self.get_object()
        if not self.object.valid:
            if self.object.invalidation_comment != "":
                msg = "WARNING: This dataset is marked invalid due to the " +\
                      "following reason: " + self.object.invalidation_comment
            else:
                msg = "WARNING: This dataset is marked invalid."
            messages.error(self.request, msg)

        if self.object.replaced_by:
            messages.warning(self.request,
                             "The dataset with UUID=" + str(self.object.id) +
                             " was replaced by the dataset with UUID=" +
                             str(self.object.replaced_by.id) + ". You were " +
                             "automatically redirected.")
            return HttpResponseRedirect(
                    reverse("scidatacontainer_db:ui-detail",
                            args=[self.object.replaced_by.id]))
        return super().get(request, pk)

    def get_object(self):
        """
        Get a :model:`scidatacontainer_db.DataSet` instance and make sure the
        requesting user has read permissions.
        """
        dataset = get_object_or_404(DataSet, id=self.kwargs["pk"])
        ensure_read_permission(self.request.user, dataset)
        return dataset


class InvalidationView(LoginRequiredMixin, generic.detail.SingleObjectMixin,
                       generic.View):
    """
    Handle the request from the invalidation modal.

    It handles PATCH and POST requests. POST request require `_method` set
    to `patch` to enable PATCH requests even thought web browsers don't support
    PATCH requests.
    """
    model = DataSet

    def post(self, request, pk):
        """
        Handle a POST request. This is a forward to the patch method if
        `_method` is `patch`.
        """
        if "_method" in self.request.POST:
            if self.request.POST["_method"] == "patch":
                self.request.PATCH = self.request.POST
                return self.patch(request, pk)
        return HttpResponseNotAllowed(["PATCH"])

    def patch(self, request, pk):
        """
        Handle a PATCH request.

        If the user is the owner of a :model:`scidatacontainer_db.DataSet`,
        store the invalidation reason and unset the `valid` flag. Afterwards,
        redirect to the overview page.
        """
        dataset = get_object_or_404(DataSet, id=pk)
        ensure_owner(request.user, dataset)

        if "confirm" in self.request.PATCH:
            dataset.valid = False
            dataset.invalidation_comment = self.request.PATCH["reason"]
            dataset.save()

            messages.info(self.request, "Dataset " + str(pk) + " was deleted.")
            return HttpResponseRedirect(
                    reverse("scidatacontainer_db:ui-index"))

        # confirm checkbox not checked -> don't do anything
        return HttpResponseRedirect(reverse("scidatacontainer_db:ui-detail",
                                            args=[pk]))


class UpdatePermissionsView(LoginRequiredMixin, generic.UpdateView):
    """
    Display a permission modification page and handle a POST request to change
    them.

    **Context**

    ``users``
        List of all available users.

    ``groups``
        List of all available groups.

    ``r_users``
        List of users with read-only permission.

    ``w_users``
        List of users with read and write permission.

    ``rw_users``
        List of users with read-only or read-and-write permission.

    ``r_groups``
        List of groups with read-only permission.

    ``w_groups``
        List of groups with read and write permission.

    ``rw_groups``
        List of groups with read-only or read-and-write permission.

    **Template**

    :template:`scidatacontainer_db/update_permissions.html`
    """
    model = DataSet
    template_name = "scidatacontainer_db/update_permissions.html"
    fields = []

    def get_context_data(self, **kwargs):
        """
        Prepare context data for the template.
        """
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.all()
        context["groups"] = Group.objects.all()

        r_users = context["dataset"].get_read_perm_user_list()
        w_users = context["dataset"].get_write_perm_user_list()
        context["r_users"] = r_users
        context["w_users"] = w_users
        context["rw_users"] = (r_users | w_users).order_by("username")

        r_groups = context["dataset"].get_read_perm_group_list()
        w_groups = context["dataset"].get_write_perm_group_list()
        context["r_groups"] = r_groups
        context["w_groups"] = w_groups
        context["rw_groups"] = (r_groups | w_groups).order_by("name")

        return context

    def get_object(self):
        """
        Check permission while finding the
        :model:`scidatacontainer_db.DataSet`.
        """
        dataset = get_object_or_404(DataSet, id=self.kwargs["pk"])
        ensure_owner(self.request.user, dataset)
        return dataset

    def post(self, request, pk):
        """
        Handle POST requests to update the permissions on an object.
        """
        dataset = get_object_or_404(DataSet, id=pk)
        ensure_owner(request.user, dataset)
        for key, val in request.POST.items():
            if key.startswith("urw_"):
                user_obj = User.objects.get(id=key[4:])
                remove_perm("change_dataset", user_obj, dataset)
                remove_perm("view_dataset", user_obj, dataset)
                if val == "ro":
                    assign_perm("view_dataset", user_obj, dataset)
                elif val == "rw":
                    assign_perm("change_dataset", user_obj, dataset)

            if key.startswith("grw_"):
                group_obj = Group.objects.get(name=key[4:])
                remove_perm("change_dataset", group_obj, dataset)
                remove_perm("view_dataset", group_obj, dataset)
                if val == "ro":
                    assign_perm("view_dataset", group_obj, dataset)
                elif val == "rw":
                    assign_perm("change_dataset", group_obj, dataset)

        if request.POST["newuser"] != "":
            try:
                user_obj = User.objects.get(username=request.POST["newuser"])
                remove_perm("change_dataset", user_obj, dataset)
                remove_perm("view_dataset", user_obj, dataset)
                if request.POST["newuser_rw-outlined"] == "ro":
                    assign_perm("view_dataset", user_obj, dataset)
                if request.POST["newuser_rw-outlined"] == "rw":
                    assign_perm("change_dataset", user_obj, dataset)
            except User.DoesNotExist:
                messages.error(request, "User \"" + request.POST["newuser"] +
                                        "\" does not exist!")

        if request.POST["newgroup"] != "":
            try:
                group_obj = Group.objects.get(name=request.POST["newgroup"])
                remove_perm("change_dataset", group_obj, dataset)
                remove_perm("view_dataset", group_obj, dataset)
                if request.POST["newgroup_rw-outlined"] == "ro":
                    assign_perm("view_dataset", group_obj, dataset)
                if request.POST["newgroup_rw-outlined"] == "rw":
                    assign_perm("change_dataset", group_obj, dataset)
            except Group.DoesNotExist:
                messages.error(request, "Group \"" + request.POST["newgroup"] +
                                        "\" does not exist!")

        if "delete-user" in request.POST:
            user_obj = User.objects.get(id=request.POST["delete-user"])
            remove_perm("change_dataset", user_obj, dataset)
            remove_perm("view_dataset", user_obj, dataset)

        if "delete-group" in request.POST:
            group_obj = Group.objects.get(name=request.POST["delete-group"])
            remove_perm("change_dataset", group_obj, dataset)
            remove_perm("view_dataset", group_obj, dataset)

        if request.POST["owner"] != "":
            try:
                user_obj = User.objects.get(username=request.POST["owner"])
                dataset.owner = user_obj
                dataset.save()
            except User.DoesNotExist:
                messages.error(request, "User \"" + request.POST["owner"] +
                                        "\" does not exist!")
                return HttpResponseRedirect(reverse("scidatacontainer_db:" +
                                                    "ui-permission_update",
                                                    args=[pk]))
            if self.request.user.has_perm("view_dataset", dataset):
                return HttpResponseRedirect(
                        reverse("scidatacontainer_db:ui-detail",
                                args=[pk]))
            return HttpResponseRedirect(
                    reverse("scidatacontainer_db:ui-index"))

        return HttpResponseRedirect(
                    reverse("scidatacontainer_db:ui-permission_update",
                            args=[pk]))


class LoginView(authviews.LoginView):
    """
    Display a login page.

    **Template**

    :template:`scidatacontainer_db/login.html`
    """
    template_name = "scidatacontainer_db/login.html"


class LogoutView(authviews.LogoutView):
    """
    Logout a user and redirect to index page.
    """
    next_page = settings.LOGOUT_REDIRECT_URL


class ApiKeyView(LoginRequiredMixin, generic.ListView):
    """
    View to list a users API keys. A post request can be used to generate a
    new API key.

    **Template**

    :template:`scidatacontainer_db/api_keys.html`
    """
    paginate_by = 10
    model = AuthToken
    template_name = "scidatacontainer_db/apikeys.html"

    def get_queryset(self):
        """
        Filter :model:`knox.AuthToken` instances to show only the ones from
        the requesting user.
        """
        q = AuthToken.objects.filter(user=self.request.user)
        return q.order_by("-created")

    def get_context_data(self, **kwargs):
        """
        Context Data function to enable pagination.
        """
        context = super().get_context_data(**kwargs)
        paginator = context["page_obj"].paginator
        page = self.request.GET.get("page", 1)
        context["page_range"] = paginator.get_elided_page_range(number=page,
                                                                on_each_side=2,
                                                                on_ends=0)
        return context

    def _delete_token(self, delete):
        """
        Delete a token if it exists and redirect to the API key overview.
        """
        token = get_object_or_404(AuthToken, digest=delete)
        token.delete()
        messages.success(self.request, "API Key deleted!")
        return HttpResponseRedirect(reverse("scidatacontainer_db:ui-keys"))

    def _create_token(self):
        """
        Create a new API key for the requesting user. The new token is
        shown as a message.
        """
        token = AuthToken.objects.create(self.request.user)[1]
        msg = """API Key created! Please remember it, this is the only time
        it is shown! {0:s}
        <button class="btn btn-link btn-msg-copy"
            id="token_{0:s}"
            data-bs-toggle="tooltip" data-vs-placement="top"
            data-bs-title="copy to clipboard">
        <svg class="bi pe-none me-2" width="24" height="24">
        <use xlink:href="#clipboard"/>
        </svg>
        </button>
        """.format(token)
        messages.success(self.request, format_html(msg))
        return HttpResponseRedirect(reverse("scidatacontainer_db:ui-keys"))

    def post(self, request):
        """
        Handle a POST request for key generation or deletion.
        """
        delete = request.POST.get("delete", False)
        if delete:
            return self._delete_token(delete)

        create = request.POST.get("create", False)
        if create:
            return self._create_token()
