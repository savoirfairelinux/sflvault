;;; Manifest for developing on SFLVault using Guix.

(use-modules (guix git-download)
             (guix packages)
             (guix build-system python)
             (gnu packages python-crypto))

;;; python-keyring > 1.6.1 API has changed, which breaks 'sflvault
;;; wallet' (see:
;;; https://github.com/savoirfairelinux/sflvault/issues/51).
(define-public python-keyring-1.6
  (package
    (inherit python-keyring)
    (version "1.6.1")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://github.com/jaraco/keyring")
             (commit "ee6fb560a3ecd17441b33a968a9243a136eb0018")))
       (file-name (git-file-name "python-keyring" version))
       (sha256
        (base32
         "1qgn1fwa3w5n5vx3nrqgxv23gqac4m9ypqk5rni4kawxax02szhx"))))
    (native-inputs '())
    (arguments
     `(#:tests? #f                  ;missing dependencies such as 'fs'
       #:phases (modify-phases %standard-phases
                  (add-after 'unpack 'patch-for-current-python
                    (lambda _
                      (substitute* (find-files "." "\\.py$")
                        (("base64.decodestring")
                         "base64.decodebytes")))))))))

(concatenate-manifests
 (list (specifications->manifest
        (list
         ;; sflvault-client dependencies.
         "python-decorator"
         "python-pexpect"
         "python-pycrypto"
         "python-urwid"

         ;; sflvault-client extra dependencies
         "openssh"

         ;; Development dependencies and tools.
         "bash"
         "coreutils"
         "grep"
         "python"
         "python-pylint"
         "python-twine"                 ;for uploading releases PyPI
         "python-virtualenv"))
       ;; Custom packages.
       (packages->manifest
        (list python-keyring-1.6))))
