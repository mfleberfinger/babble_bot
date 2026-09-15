import gc
import random
import threading
from enum import Enum

import ctranslate2

import argos_setup  # noqa: F401 - must run before argostranslate import
from argostranslate.package import get_installed_packages
from argostranslate.sbd import MiniSBDSentencizer
from argostranslate.translate import apply_packaged_translation

# Codes users may still type from the old googletrans days.
LANGUAGE_ALIASES = {
    "zh-cn": "zh",
    "zh-tw": "zt",
    "zh-hans": "zh",
    "zh-hant": "zt",
    "pt-br": "pb",
    "iw": "he",
    "no": "nb",
    "fil": "tl",
}

# CTranslate2 models are large; only one hop should hold a model at a time.
_translate_lock = threading.Lock()
_MAX_OUTPUT_CHARS = 4000


class MangleMethod(Enum):
    flipflop = 1
    straight = 2
    manual = 3

    def __str__(self):
        if self == MangleMethod.flipflop:
            return "flip flop: flip flop between a primary language and random languages."
        elif self == MangleMethod.straight:
            return "straight: run through a completely random list of languages."
        elif self == MangleMethod.manual:
            return "manual: language path specified by the user manually."
        else:
            raise NotImplementedError(
                "MangleMethod value's __str__ conversion not implemented.")


def _load_packages():
    packages = {}
    for pkg in get_installed_packages():
        if getattr(pkg, "type", "translate") != "translate":
            continue
        if pkg.from_code and pkg.to_code:
            packages[(pkg.from_code, pkg.to_code)] = pkg
    return packages


def _language_codes(packages):
    codes = set()
    for src, dest in packages:
        codes.add(src)
        codes.add(dest)
    return codes


def _resolve_language_code(code, available):
    if not code:
        return None
    code = code.lower()
    if code in available:
        return code
    alias = LANGUAGE_ALIASES.get(code)
    if alias in available:
        return alias
    return None


def _clip_output(text):
    if len(text) > _MAX_OUTPUT_CHARS:
        return text[:_MAX_OUTPUT_CHARS]
    return text


def _translate_with_package(text, pkg):
    translator = ctranslate2.Translator(
        str(pkg.package_path / "model"),
        device="cpu",
        inter_threads=1,
        intra_threads=0,
    )
    try:
        sentencizer = MiniSBDSentencizer(pkg)
        hypotheses = apply_packaged_translation(
            pkg, text, translator, sentencizer, num_hypotheses=1)
        return _clip_output(hypotheses[0].value)
    finally:
        unload = getattr(translator, "unload_model", None)
        if callable(unload):
            unload()
        del translator
        gc.collect()


def _translate(text, src, dest, packages):
    if src == dest:
        return text
    pkg = packages.get((src, dest))
    if pkg is not None:
        return _translate_with_package(text, pkg)
    # Official packages are mostly XX↔en; pivot through English.
    to_en = packages.get((src, "en"))
    from_en = packages.get(("en", dest))
    if to_en is not None and from_en is not None:
        pivoted = _translate_with_package(text, to_en)
        return _translate_with_package(pivoted, from_en)
    raise ValueError("No translation path {} -> {}".format(src, dest))


class Mangle:
    def __init__(self, language, low, high, language_blacklist):
        self.language = language
        self._packages = _load_packages()
        available = _language_codes(self._packages)
        if not available:
            raise RuntimeError(
                "No Argos Translate packages found in {}. "
                "Run: python3 download_argos_packages.py".format(
                    argos_setup.PACKAGES_DIR))
        self.languages = available - set(language_blacklist)
        self.low = low
        self.high = high

    def mangle(self, message_text, times=0, method=None, language_list=None):

        if method == MangleMethod.manual and not language_list:
            raise ValueError("No language list given.")
        if method is None:
            method = random.sample(
                list(set(MangleMethod) - set([MangleMethod.manual])), 1)[0]
        if times < 0:
            raise ValueError("Parameter times must be greater than 0.")
        if times == 0:
            times = random.randint(self.low, self.high)

        pool = list(self.languages)
        if method == MangleMethod.manual:
            resolved = []
            known = self.languages | {self.language}
            for code in language_list:
                resolved_code = _resolve_language_code(code, known)
                resolved.append(code if resolved_code is None else resolved_code)
            language_list = resolved
            language_list.insert(0, self.language)
            language_list.append(self.language)
        elif method == MangleMethod.flipflop:
            language_list = []
            language_list.append(self.language)
            for i in range(int(times / 2)):
                language_list.extend(
                    [random.choice(pool), self.language])
        elif method == MangleMethod.straight:
            language_list = []
            language_list.append(self.language)
            if times <= len(pool):
                language_list.extend(random.sample(pool, times))
            else:
                language_list.extend(random.choices(pool, k=times))
            language_list.append(self.language)
        else:
            raise NotImplementedError(
                "MangleMethod {} not implemented.".format(method))

        all_messages = self._translate_path(message_text, language_list)

        message_info = {
            'method': str(method),
            'languages': language_list,
            'all_messages': all_messages
        }

        return message_info

    def _translate_path(self, message_text, language_list):
        all_messages = [message_text]
        with _translate_lock:
            for i in range(1, len(language_list)):
                src = language_list[i - 1]
                dest = language_list[i]
                try:
                    text = _translate(
                        all_messages[i - 1], src, dest, self._packages)
                    all_messages.append(text)
                except Exception as e:
                    print("translate failed {} -> {}: {}".format(src, dest, e))
                    all_messages = False
                    break

        return all_messages
