/* ============================================================
   Study Planner — 共通UIヘルパー
   base.html から全ページで読み込まれる。
     showToast(msg, type)                    … トースト通知
     showConfirm({title,message,okLabel,danger}) … Promise<boolean> を返す確認モーダル
     <form data-confirm="...">               … submit時に自動でモーダル確認
   ============================================================ */
(function () {
  'use strict';

  /* ---------- トースト ---------- */
  var toastTimer = null;

  function showToast(msg, type) {
    var t = document.getElementById('toast');
    if (!t) { return; }
    var kind = type || 'success';
    t.textContent = msg;
    t.className = 'show ' + kind;
    if (toastTimer) { clearTimeout(toastTimer); }
    toastTimer = setTimeout(function () { t.className = ''; }, 3000);
  }

  /* ---------- 確認モーダル ---------- */
  var confirmState = null;   // { resolve, prevFocus }

  function modalEls() {
    return {
      modal: document.getElementById('confirm-modal'),
      title: document.getElementById('confirm-title'),
      message: document.getElementById('confirm-message'),
      ok: document.getElementById('confirm-ok'),
      cancel: document.getElementById('confirm-cancel')
    };
  }

  function closeConfirm(result) {
    var e = modalEls();
    if (!e.modal) { return; }
    e.modal.classList.remove('show');
    e.modal.classList.remove('danger');
    var st = confirmState;
    confirmState = null;
    if (st) {
      if (st.prevFocus && st.prevFocus.focus) {
        try { st.prevFocus.focus(); } catch (_) { /* noop */ }
      }
      st.resolve(!!result);
    }
  }

  /**
   * 確認モーダルを開く。
   * @param {Object} opts {title, message, okLabel, danger}
   * @returns {Promise<boolean>} OK なら true
   */
  function showConfirm(opts) {
    var o = opts || {};
    var e = modalEls();

    // モーダルが無いページではブラウザネイティブにフォールバック
    if (!e.modal) {
      return Promise.resolve(window.confirm(o.message || o.title || 'OK?'));
    }

    // 既に開いている場合は先のものをキャンセル扱いで閉じる
    if (confirmState) { closeConfirm(false); }

    if (e.title)   { e.title.textContent = o.title || 'Confirm'; }
    if (e.message) { e.message.textContent = o.message || ''; }
    if (e.ok) {
      e.ok.textContent = o.okLabel || 'OK';
      e.ok.className = 'btn btn-sm ' + (o.danger === false ? 'btn-primary' : 'btn-danger');
    }
    if (o.danger === false) {
      e.modal.classList.remove('danger');
    } else {
      e.modal.classList.add('danger');
    }
    e.modal.classList.add('show');

    var prevFocus = document.activeElement;
    if (e.ok && e.ok.focus) { e.ok.focus(); }

    return new Promise(function (resolve) {
      confirmState = { resolve: resolve, prevFocus: prevFocus };
    });
  }

  /* ---------- 初期化 ---------- */
  function init() {
    var e = modalEls();
    if (e.modal) {
      if (e.ok)     { e.ok.addEventListener('click', function () { closeConfirm(true); }); }
      if (e.cancel) { e.cancel.addEventListener('click', function () { closeConfirm(false); }); }
      e.modal.addEventListener('click', function (ev) {
        if (ev.target === e.modal) { closeConfirm(false); }
      });
    }

    // Esc で閉じる
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && confirmState) {
        ev.preventDefault();
        closeConfirm(false);
      }
    });

    // <form data-confirm="本当に削除しますか？"> を自動でモーダル確認に通す
    document.addEventListener('submit', function (ev) {
      var form = ev.target;
      if (!form || !form.getAttribute) { return; }
      var msg = form.getAttribute('data-confirm');
      if (!msg) { return; }
      if (form.dataset.confirmed === '1') {
        delete form.dataset.confirmed;
        return;   // モーダルOK後の再submitはそのまま通す
      }
      ev.preventDefault();
      showConfirm({
        title: form.getAttribute('data-confirm-title') || 'Confirm',
        message: msg,
        okLabel: form.getAttribute('data-confirm-ok') || 'OK',
        danger: form.getAttribute('data-confirm-danger') !== 'false'
      }).then(function (ok) {
        if (ok) {
          form.dataset.confirmed = '1';
          if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
          } else {
            form.submit();
          }
        }
      });
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ---------- 公開 ---------- */
  window.showToast = showToast;
  window.showConfirm = showConfirm;
  window.closeConfirm = closeConfirm;
})();
