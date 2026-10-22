# Independent verifier task prompt

Verify TASK_ID at exact PR_HEAD_SHA against BASE_SHA in a detached workspace. You did not author the implementation being accepted. Read the assignment, model/design and handoff. Independently reproduce the relevant acceptance checks; inspect numerical assumptions and ownership boundaries. Record pass/fail/blocked with evidence and environment IDs.

Do not merge. Do not quietly fix implementation while approving it. If you create a fix commit, return its new head for a fresh verification cycle. A model review under the author's GitHub account is useful evidence but does not impersonate a distinct required GitHub approval actor.
