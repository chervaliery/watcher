(function () {
  'use strict';

  var THEME_KEY = 'watcher-theme';

  angular.module('watcherApp', ['ngRoute'])
    .constant('API_BASE', '/api/')
    .controller('ThemeController', function () {
      var vm = this;
      var stored = typeof localStorage !== 'undefined' && localStorage.getItem(THEME_KEY);
      vm.isDark = stored !== 'light';
      vm.toggle = function () {
        vm.isDark = !vm.isDark;
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(THEME_KEY, vm.isDark ? 'dark' : 'light');
        }
      };
    })
    .config(function ($routeProvider, $locationProvider) {
      $locationProvider.hashPrefix('');
      $routeProvider
        .when('/', {
          templateUrl: '/static/dashboard/partials/dashboard.html',
          controller: 'DashboardController',
          controllerAs: 'vm'
        })
        .when('/applications', {
          templateUrl: '/static/dashboard/partials/applications.html',
          controller: 'ApplicationsController',
          controllerAs: 'vm'
        })
        .when('/applications/:id/history', {
          templateUrl: '/static/dashboard/partials/application-history.html',
          controller: 'ApplicationHistoryController',
          controllerAs: 'vm'
        })
        .otherwise({ redirectTo: '/' });
    })
    .service('api', function ($http, API_BASE) {
      this.getDashboard = function () {
        return $http.get(API_BASE + 'dashboard/');
      };
      this.getApplications = function () {
        return $http.get(API_BASE + 'applications/');
      };
      this.getApplication = function (id) {
        return $http.get(API_BASE + 'applications/' + id + '/');
      };
      this.createApplication = function (data) {
        return $http.post(API_BASE + 'applications/', data);
      };
      this.updateApplication = function (id, data) {
        return $http({
          method: 'PATCH',
          url: API_BASE + 'applications/' + id + '/',
          data: data,
          headers: { 'Content-Type': 'application/json' }
        });
      };
      this.deleteApplication = function (id) {
        return $http.delete(API_BASE + 'applications/' + id + '/');
      };
      this.getHistory = function (id, page, pageSize) {
        page = page || 1;
        pageSize = pageSize || 20;
        return $http.get(API_BASE + 'applications/' + id + '/history/', {
          params: { page: page, page_size: pageSize }
        });
      };
    })
    .controller('DashboardController', function (api, $interval) {
      var vm = this;
      vm.items = [];
      vm.loading = true;
      vm.error = null;

      function load() {
        vm.loading = true;
        vm.error = null;
        api.getDashboard().then(function (res) {
          vm.items = res.data.items || [];
          vm.loading = false;
        }).catch(function (err) {
          vm.error = err.data && err.data.error ? err.data.error : 'Failed to load dashboard';
          vm.loading = false;
        });
      }

      load();
      vm.refreshInterval = $interval(load, 45000);

      vm.isActive = function (item) {
        return item.application && item.application.is_active;
      };
      vm.isInactive = function (item) {
        return item.application && !item.application.is_active;
      };

      vm.$onDestroy = function () {
        if (vm.refreshInterval) {
          $interval.cancel(vm.refreshInterval);
        }
      };
    })
    .controller('ApplicationsController', function (api, $location) {
      var vm = this;
      vm.apps = [];
      vm.loading = true;
      vm.error = null;
      vm.editId = null;
      vm.form = {};
      vm.formError = null;
      vm.formSuccess = null;
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/d8fc5cc9-d7fb-465a-8b5b-9a54c612ff5f', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'app.js:ApplicationsController entry', message: 'controller entry', data: { hypothesisId: 'C' }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(function () {});
      } catch (e) {}
      // #endregion

      function load() {
        vm.loading = true;
        api.getApplications().then(function (res) {
          vm.apps = (res.data.results || []);
          vm.loading = false;
        }).catch(function () {
          vm.error = 'Failed to load applications';
          vm.loading = false;
        });
      }

      load();

      vm.startAdd = function () {
        // #region agent log
        try {
          fetch('http://127.0.0.1:7242/ingest/d8fc5cc9-d7fb-465a-8b5b-9a54c612ff5f', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'app.js:startAdd', message: 'startAdd invoked', data: { hypothesisId: 'B' }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(function () {});
        } catch (e) {}
        // #endregion
        vm.editId = null;
        vm.form = {
          name: '',
          base_url: '',
          hostname: '',
          check_interval_seconds: 60,
          is_active: true,
          client_p12_path: '',
          client_p12_password: '',
          ca_bundle_path: ''
        };
        vm.formError = null;
        vm.formSuccess = null;
      };
      // #region agent log
      try {
        fetch('http://127.0.0.1:7242/ingest/d8fc5cc9-d7fb-465a-8b5b-9a54c612ff5f', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'app.js:after startAdd def', message: 'after startAdd defined', data: { typeof_startAdd: typeof vm.startAdd, hypothesisId: 'A' }, timestamp: Date.now(), sessionId: 'debug-session' }) }).catch(function () {});
      } catch (e) {}
      // #endregion

      vm.startEdit = function (app) {
        vm.editId = app.id;
        vm.form = {
          name: app.name,
          base_url: app.base_url,
          hostname: app.hostname || '',
          check_interval_seconds: app.check_interval_seconds,
          is_active: app.is_active,
          client_p12_path: app.client_p12_path || '',
          client_p12_password: app.client_p12_password || '',
          ca_bundle_path: app.ca_bundle_path || ''
        };
        vm.formError = null;
        vm.formSuccess = null;
      };

      vm.save = function () {
        vm.formError = null;
        vm.formSuccess = null;
        if (!vm.form.base_url || !vm.form.base_url.trim()) {
          vm.formError = 'Base URL is required';
          return;
        }
        var payload = {
          name: vm.form.name || vm.form.base_url,
          base_url: vm.form.base_url.trim(),
          hostname: vm.form.hostname.trim(),
          check_interval_seconds: parseInt(vm.form.check_interval_seconds, 10) || 60,
          is_active: vm.form.is_active,
          client_p12_path: (vm.form.client_p12_path || '').trim(),
          client_p12_password: (vm.form.client_p12_password || '').trim(),
          ca_bundle_path: (vm.form.ca_bundle_path || '').trim()
        };
        if (vm.editId) {
          api.updateApplication(vm.editId, payload).then(function () {
            vm.formSuccess = 'Saved.';
            load();
            vm.editId = null;
          }).catch(function (err) {
            vm.formError = (err.data && err.data.error) ? err.data.error : 'Update failed';
          });
        } else {
          api.createApplication(payload).then(function () {
            vm.formSuccess = 'Created.';
            load();
            vm.form = {};
          }).catch(function (err) {
            vm.formError = (err.data && err.data.error) ? err.data.error : 'Create failed';
          });
        }
      };

      vm.remove = function (app) {
        if (!confirm('Delete "' + (app.name || app.base_url) + '"?')) return;
        api.deleteApplication(app.id).then(function () {
          load();
        });
      };

      vm.cancelEdit = function () {
        vm.editId = null;
        vm.formError = null;
        vm.formSuccess = null;
      };

      vm.startAdd(); // initialize form for "Add" (must run after startAdd is defined)
    })
    .controller('ApplicationHistoryController', function (api, $routeParams, $location) {
      var vm = this;
      vm.appId = $routeParams.id;
      vm.results = [];
      vm.total = 0;
      vm.page = 1;
      vm.pageSize = 20;
      vm.loading = true;
      vm.appName = '';

      function load() {
        vm.loading = true;
        api.getApplication(vm.appId).then(function (res) {
          vm.appName = res.data.name || res.data.base_url;
        });
        api.getHistory(vm.appId, vm.page, vm.pageSize).then(function (res) {
          vm.results = res.data.results || [];
          vm.total = res.data.total || 0;
          vm.loading = false;
        }).catch(function () {
          vm.loading = false;
        });
      }

      vm.prevPage = function () {
        if (vm.page > 1) {
          vm.page--;
          load();
        }
      };

      vm.nextPage = function () {
        if ((vm.page * vm.pageSize) < vm.total) {
          vm.page++;
          load();
        }
      };

      load();
    });
})();
