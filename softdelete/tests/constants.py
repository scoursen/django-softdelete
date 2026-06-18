from softdelete.test_softdelete_app.models import TestModelTwoCascade, TestModelTwoDoNothing, TestModelTwoSetNull

TEST_MODEL_ONE_COUNT = 2
TEST_MODEL_TWO_TOTAL_COUNT = 12  # should be multiple of LCM(TEST_MODEL_ONE_COUNT,TEST_MODEL_TWO_COUNT),
# here LCM is 6 and multiplier is 2

TEST_MODEL_THREE_COUNT = TEST_MODEL_TWO_TOTAL_COUNT ** 2
TEST_MODEL_TWO_LIST = [TestModelTwoCascade,
                       TestModelTwoDoNothing,
                       TestModelTwoSetNull]
TEST_MODEL_TWO_CASCADE_COUNT = TEST_MODEL_TWO_DO_NOTHING_COUNT = TEST_MODEL_TWO_SET_NULL_COUNT = \
    TEST_MODEL_TWO_TOTAL_COUNT // len(TEST_MODEL_TWO_LIST)
